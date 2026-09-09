"""A bounded JSON Schema subset for public execution, with cooperative work limits.

No references, regexes, combinators, uniqueness scans or schema-valued metadata.
Every supported validator is linear in a bounded JSON tree. A shared operation
budget and deadline also bound repeated property/item validation.
"""

from __future__ import annotations

import math
import threading
import time
from collections.abc import Callable
from typing import Any, cast

from jsonschema import Draft202012Validator, validators

_KEYWORDS = {
    "type",
    "properties",
    "required",
    "additionalProperties",
    "items",
    "prefixItems",
    "minItems",
    "maxItems",
    "minLength",
    "maxLength",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "minProperties",
    "maxProperties",
    "enum",
    "const",
    "title",
    "description",
    "$schema",
    "default",
    "examples",
}
_SCALAR = (str, int, float, bool, type(None))


def validate_schema(schema: Any) -> None:
    nodes = 0

    def count(value: Any, depth: int = 0) -> None:
        nonlocal nodes
        nodes += 1
        if nodes > 512 or depth > 24:
            raise ValueError("schema exceeds the supported complexity bound")
        if isinstance(value, dict):
            for child in value.values():
                count(child, depth + 1)
        elif isinstance(value, list):
            for child in value:
                count(child, depth + 1)
        elif isinstance(value, str) and len(value) > 4096:
            raise ValueError("schema string exceeds the supported bound")
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            if not math.isfinite(value) or abs(value) > 1e100:
                raise ValueError("schema number exceeds the supported bound")

    def visit(value: Any) -> None:
        if isinstance(value, bool):
            return
        if not isinstance(value, dict):
            raise ValueError("schema must be an object or boolean")
        unsupported = value.keys() - _KEYWORDS
        if unsupported:
            raise ValueError("unsupported schema keyword: " + sorted(unsupported)[0])
        if "const" in value and not isinstance(value["const"], _SCALAR):
            raise ValueError("const supports only scalar JSON values")
        if "enum" in value and (
            not isinstance(value["enum"], list)
            or len(value["enum"]) > 32
            or not all(isinstance(item, _SCALAR) for item in value["enum"])
        ):
            raise ValueError("enum supports at most 32 scalar JSON values")
        properties = value.get("properties", {})
        if not isinstance(properties, dict):
            raise ValueError("properties must be an object")
        for child in properties.values():
            visit(child)
        for key in ("items", "additionalProperties"):
            if key in value:
                visit(value[key])
        for child in value.get("prefixItems", []):
            visit(child)

    try:
        count(schema)
        visit(schema)
        Draft202012Validator.check_schema(schema)
    except (OverflowError, TypeError, RecursionError) as exc:
        raise ValueError("schema exceeds the supported complexity bound") from exc


def validate_instance(
    schema: Any,
    value: Any,
    *,
    deadline: float | None = None,
    cancel_event: threading.Event | None = None,
) -> None:
    deadline = min(deadline if deadline is not None else math.inf, time.monotonic() + 1)
    remaining = 50_000
    data_nodes = 0
    size = 0

    def check() -> None:
        nonlocal remaining
        remaining -= 1
        if (
            remaining < 0
            or time.monotonic() >= deadline
            or (cancel_event is not None and cancel_event.is_set())
        ):
            raise ValueError("validation canceled or exceeded its work/deadline bound")

    def walk(item: Any, depth: int = 0) -> None:
        nonlocal data_nodes, size
        check()
        data_nodes += 1
        if depth > 24 or data_nodes > 10_000:
            raise ValueError("JSON data exceeds the supported complexity bound")
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    raise ValueError("JSON object keys must be strings")
                size += len(key)
                walk(child, depth + 1)
        elif isinstance(item, list):
            for child in item:
                walk(child, depth + 1)
        elif isinstance(item, str):
            size += len(item)
        elif isinstance(item, (int, float)) and not isinstance(item, bool):
            try:
                if not math.isfinite(item) or abs(item) > 1e100:
                    raise ValueError("JSON number exceeds the supported bound")
            except OverflowError as exc:
                raise ValueError("JSON number exceeds the supported bound") from exc
        elif not isinstance(item, (bool, type(None))):
            raise ValueError("value must be JSON")
        if size > 1024 * 1024:
            raise ValueError("JSON data exceeds 1 MiB")

    def guarded(original: Any) -> Any:
        def validate(validator: Any, constraint: Any, instance: Any, definition: Any) -> Any:
            check()
            yield from original(validator, constraint, instance, definition)

        return validate

    check()
    validate_schema(schema)
    walk(value)
    bounded = cast(Callable[..., Any], validators.extend)(
        Draft202012Validator,
        {
            key: guarded(fn)
            for key, fn in Draft202012Validator.VALIDATORS.items()
            if key in _KEYWORDS
        },
    )
    bounded(schema).validate(value)
    check()
