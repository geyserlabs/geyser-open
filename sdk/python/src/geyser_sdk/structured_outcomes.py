"""Versioned, self-contained structured outcome contracts."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from pydantic import JsonValue, RootModel, model_validator

from ._json import bytes_digest, digest

SCHEMA_VERSION = 1
MAX_CONTRACT_BYTES = 128 * 1024
MAX_OUTCOME_BYTES = 8 * 1024 * 1024
_LOCAL_REF = re.compile(r"^(?:#(?:/.*)?)?$")


class OutcomeContractError(ValueError):
    """The trusted outcome contract is malformed or unsafe."""


class OutcomeValidationError(ValueError):
    """A result does not satisfy the exact outcome contract."""


def _walk_refs(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in {"$ref", "$dynamicRef"} and _LOCAL_REF.fullmatch(str(child or "")) is None:
                raise OutcomeContractError("outcome schemas may use only local references")
            _walk_refs(child)
    elif isinstance(value, list):
        for child in value:
            _walk_refs(child)


def normalize_contract(value: Any) -> dict[str, Any] | None:
    if value in (None, {}):
        return None
    if not isinstance(value, Mapping):
        raise OutcomeContractError("structured outcome contract must be an object")
    try:
        encoded = json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode()
    except (TypeError, ValueError) as exc:
        raise OutcomeContractError("structured outcome contract must be finite JSON") from exc
    if len(encoded) > MAX_CONTRACT_BYTES:
        raise OutcomeContractError("structured outcome contract exceeds 128 KiB")
    if int(value.get("schema_version") or 0) != SCHEMA_VERSION:
        raise OutcomeContractError("unsupported structured outcome contract version")
    schema = value.get("json_schema")
    if not isinstance(schema, dict):
        raise OutcomeContractError("structured outcome contract requires json_schema")
    _walk_refs(schema)
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:  # jsonschema exposes several validation subclasses
        raise OutcomeContractError(f"invalid Draft 2020-12 outcome schema: {exc}") from exc
    schema_ref = str(value.get("schema_ref") or "").strip()
    if not schema_ref or len(schema_ref) > 512:
        raise OutcomeContractError("structured outcome contract requires schema_ref")
    revision = str(value.get("schema_revision") or "1").strip()
    if not revision or len(revision) > 80:
        raise OutcomeContractError("structured outcome schema_revision is invalid")
    title = str(value.get("title") or schema.get("title") or "Structured outcome")
    if len(title) > 240:
        raise OutcomeContractError("structured outcome title is too long")
    normalized: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "schema_ref": schema_ref,
        "schema_revision": revision,
        "title": title,
        "description": str(value.get("description") or "")[:2000],
        "json_schema": schema,
        "require_evidence_refs": bool(value.get("require_evidence_refs", False)),
    }
    normalized["schema_digest"] = digest(schema)
    normalized["contract_digest"] = digest(normalized)
    return normalized


def evidence_refs(value: Any) -> list[str]:
    refs: set[str] = set()

    def walk(current: Any, key: str = "") -> None:
        if isinstance(current, Mapping):
            for child_key, child in current.items():
                walk(child, str(child_key).casefold())
        elif isinstance(current, list):
            for child in current[:10000]:
                walk(child, key)
        elif isinstance(current, str) and (
            key.endswith("_ref")
            or key.endswith("_refs")
            or key in {"evidence", "artifacts", "sources"}
        ):
            if current.strip() and len(current) <= 1024:
                refs.add(current.strip())

    walk(value)
    return sorted(refs)[:1024]


def validate_outcome(contract: Mapping[str, Any], value: Any) -> Any:
    try:
        encoded = json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode()
    except (TypeError, ValueError) as exc:
        raise OutcomeValidationError("outcome is not finite JSON") from exc
    if len(encoded) > MAX_OUTCOME_BYTES:
        raise OutcomeValidationError("outcome exceeds the 8 MiB bound")
    validator = Draft202012Validator(
        dict(contract["json_schema"]), format_checker=FormatChecker()
    )
    errors = sorted(validator.iter_errors(value), key=lambda item: list(item.absolute_path))
    if errors:
        error = errors[0]
        path = "/".join(str(item) for item in error.absolute_path) or "$"
        raise OutcomeValidationError(
            f"outcome schema validation failed at {path}: {error.validator}"
        )
    if contract.get("require_evidence_refs") and not evidence_refs(value):
        raise OutcomeValidationError("outcome requires at least one evidence reference")
    return value


def parse_candidate(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    candidate = value.strip()
    if candidate.startswith("```json") and candidate.endswith("```"):
        candidate = candidate[7:-3].strip()
    elif candidate.startswith("```") and candidate.endswith("```"):
        candidate = candidate[3:-3].strip()
    if not candidate or candidate[0] not in "[{" or candidate[-1] not in "]}":
        raise OutcomeValidationError("structured outcome was not an exact JSON object or array")
    try:
        return json.loads(candidate)
    except (TypeError, ValueError) as exc:
        raise OutcomeValidationError("structured outcome was not valid JSON") from exc


def pydantic_output_type(contract: Mapping[str, Any]) -> Any:
    schema = dict(contract["json_schema"])

    class ContractOutcome(RootModel[JsonValue]):
        @model_validator(mode="after")
        def exact_contract(self) -> ContractOutcome:
            validate_outcome(contract, self.root)
            return self

        @classmethod
        def __get_pydantic_json_schema__(cls, _core_schema: Any, _handler: Any) -> dict[str, Any]:
            return schema

    ContractOutcome.__name__ = "GeyserStructuredOutcome"
    ContractOutcome.__qualname__ = "GeyserStructuredOutcome"
    return ContractOutcome


def checkpoint_value(contract: Mapping[str, Any], value: Any) -> dict[str, Any]:
    validate_outcome(contract, value)
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode()
    return {
        "schema_version": SCHEMA_VERSION,
        "schema_ref": str(contract["schema_ref"]),
        "schema_revision": str(contract["schema_revision"]),
        "schema_digest": str(contract["schema_digest"]),
        "contract_digest": str(contract["contract_digest"]),
        "payload": value,
        "payload_digest": bytes_digest(encoded),
        "evidence_refs": evidence_refs(value),
        "validation_state": "accepted",
    }


__all__ = [
    "OutcomeContractError",
    "OutcomeValidationError",
    "checkpoint_value",
    "evidence_refs",
    "normalize_contract",
    "parse_candidate",
    "pydantic_output_type",
    "validate_outcome",
]
