from __future__ import annotations

import math

import pytest
from geyser_sdk import (
    OutcomeContractError,
    OutcomeValidationError,
    TaskCreate,
    TypedTask,
    checkpoint_value,
    digest,
    evidence_refs,
    normalize_contract,
    parse_candidate,
    pydantic_output_type,
    validate_outcome,
)
from pydantic import ValidationError

SHA = "sha256:" + "a" * 64


def contract(*, evidence: bool = False) -> dict[str, object]:
    value = normalize_contract({
        "schema_version": 1,
        "schema_ref": "example:answer:v1",
        "json_schema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {"answer": {"type": "string"}, "evidence_ref": {"type": "string"}},
            "required": ["answer"],
            "additionalProperties": False,
        },
        "require_evidence_refs": evidence,
    })
    assert value is not None
    return value


def test_strict_inputs_and_additive_outputs() -> None:
    task = TaskCreate(input_ref="artifact:prompt-1", input_digest=SHA)
    assert task.input_ref
    with pytest.raises(ValidationError):
        TaskCreate(input_ref="artifact:prompt-1", input_digest=SHA, future="x")  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        TaskCreate(input_ref="not opaque", input_digest=SHA)
    with pytest.raises(ValidationError):
        TypedTask(task_id="t", context_id="c", prompt_digest="nope")
    with pytest.raises(ValueError, match="finite JSON"):
        digest({"not_finite": math.nan})


def test_outcome_validation_and_checkpoint() -> None:
    normalized = contract(evidence=True)
    value = {"answer": "yes", "evidence_ref": "artifact:proof"}
    assert validate_outcome(normalized, value) == value
    assert evidence_refs(value) == ["artifact:proof"]
    checkpoint = checkpoint_value(normalized, value)
    assert checkpoint["payload_digest"].startswith("sha256:")
    assert parse_candidate("```json\n{\"answer\":\"yes\"}\n```") == {"answer": "yes"}
    output_type = pydantic_output_type(normalized)
    assert output_type.model_validate(value).root == value


def test_outcome_rejects_remote_refs_invalid_values_and_prose() -> None:
    with pytest.raises(OutcomeContractError, match="local references"):
        normalize_contract({
            "schema_version": 1,
            "schema_ref": "bad:v1",
            "json_schema": {"$ref": "https://attacker.example/schema"},
        })
    with pytest.raises(OutcomeValidationError, match="requires"):
        validate_outcome(contract(evidence=True), {"answer": "no proof"})
    with pytest.raises(OutcomeValidationError, match="additionalProperties"):
        validate_outcome(contract(), {"answer": "yes", "secret": True})
    with pytest.raises(OutcomeValidationError, match="exact JSON"):
        parse_candidate("The answer is {}")
