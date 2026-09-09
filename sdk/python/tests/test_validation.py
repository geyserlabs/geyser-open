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
