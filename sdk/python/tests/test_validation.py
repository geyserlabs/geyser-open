from __future__ import annotations

import threading
import time

import pytest
from geyser_sdk.validation import validate_instance, validate_schema
from jsonschema.exceptions import ValidationError


@pytest.mark.parametrize(
    "keyword",
    [
        "uniqueItems",
        "contains",
        "allOf",
        "anyOf",
        "oneOf",
        "not",
        "$ref",
        "pattern",
        "format",
        "dependentSchemas",
    ],
)
def test_expensive_schema_work_is_rejected(keyword: str) -> None:
    with pytest.raises(ValueError, match="unsupported schema keyword"):
        validate_schema({"type": "array", keyword: True})


def test_cancel_and_work_bounds_cover_validation() -> None:
    payload = [{"n": i} for i in range(5000)]
    start = time.monotonic()
    with pytest.raises(ValueError, match="unsupported schema keyword"):
        validate_instance({"type": "array", "uniqueItems": True}, payload)
    assert time.monotonic() - start < 0.25
    stop = threading.Event()
    stop.set()
    with pytest.raises(ValueError, match="canceled"):
        validate_instance({}, payload, cancel_event=stop)
    with pytest.raises(ValueError, match="deadline"):
        validate_instance({}, payload, deadline=time.monotonic() - 1)
    with pytest.raises(ValueError, match="complexity"):
        validate_instance({}, list(range(10001)))


def test_supported_nested_contract_and_scalar_enumeration() -> None:
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "required": ["n"],
            "properties": {"n": {"type": "integer", "minimum": 0, "enum": [1, 2]}},
            "additionalProperties": False,
        },
        "maxItems": 10,
    }
    validate_instance(schema, [{"n": 1}, {"n": 2}])
    with pytest.raises(ValidationError):
        validate_instance(schema, [{"n": -1}])
    with pytest.raises(ValueError, match="scalar"):
        validate_schema({"enum": [{"nested": "object"}]})


@pytest.mark.parametrize(
    "schema",
    [
        {"properties": []},
        {"items": "invalid"},
        {"const": {}},
        {"enum": list(range(33))},
        {"maximum": 1e101},
        {"maximum": 10**1000},
        {"title": "x" * 4097},
        {"properties": {f"n{i}": True for i in range(513)}},
    ],
)
def test_malformed_or_oversized_schemas_are_rejected(schema: object) -> None:
    with pytest.raises(ValueError):
        validate_schema(schema)


@pytest.mark.parametrize(
    "value",
    [
        {1: "invalid"},
        {"n": float("inf")},
        10**1000,
        {"unexpected": object()},
        "x" * (1024 * 1024 + 1),
    ],
)
def test_non_json_and_oversized_values_are_rejected(value: object) -> None:
    with pytest.raises(ValueError):
        validate_instance({}, value)


def test_prefix_items_and_depth_bounds() -> None:
    validate_instance({"type": "array", "prefixItems": [{"type": "integer"}], "items": False}, [1])
    nested: object = 0
    for _ in range(25):
        nested = [nested]
    with pytest.raises(ValueError, match="complexity"):
        validate_instance({}, nested)
