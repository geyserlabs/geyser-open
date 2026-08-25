"""Canonical, expiring qualification receipts and evidence-derived capability matrices."""

from __future__ import annotations

import hashlib
import json
import re
import time
from collections.abc import Iterable, Mapping
from typing import Any

LAYERS = frozenset({
    "protocol_core",
    "runtime_adapter",
    "provider_transport",
    "model_delta",
    "placement_privacy",
    "developer_artifact",
})

REQUIRED_CASES: dict[str, frozenset[str]] = {
    "protocol_core": frozenset({
        "admission-before-model",
        "denial-before-model",
        "duplicate-event",
        "out-of-order-event",
        "effectless-classification",
        "consequential-classification",
        "approval-bind",
        "approval-expire",
        "approval-deny",
        "approval-argument-drift",
        "unknown-effect-reconciliation",
        "privacy-cross-tenant-denial",
        "deletion-propagation",
        "old-agent-new-cell",
        "new-agent-old-cell",
    }),
    "runtime_adapter": frozenset({
        "three-turn-continuity",
        "crash-before-durable-event",
        "crash-after-durable-event",
        "lost-acknowledgement",
        "serial-tool-calls",
        "parallel-tool-calls",
        "malformed-tool-call",
        "cancel-before-model",
        "cancel-during-stream",
        "cancel-during-tool",
        "cancel-during-specialist",
        "context-compaction",
        "model-migration",
        "structured-outcome-valid",
        "structured-outcome-invalid",
        "structured-outcome-repair-exhausted",
        "specialist-concurrency",
        "specialist-depth",
        "specialist-read-only",
        "specialist-typed-result",
        "trace-without-hidden-reasoning",
        "safe-replay",
        "safe-fork",
    }),
    "provider_transport": frozenset({
        "transport-streaming",
        "transport-usage",
        "transport-errors",
        "transport-cancellation",
        "transport-tool-continuation",
        "hard-budget-boundary",
        "soft-budget-boundary",
    }),
    "model_delta": frozenset({"exact-model-profile-delta"}),
    "placement_privacy": frozenset({
        "placement-identity",
        "custody-posture",
        "placement-privacy-denial",
    }),
    "developer_artifact": frozenset({
        "sdk-clean-install",
        "sdk-clean-uninstall",
        "cli-clean-install",
        "cli-clean-uninstall",
        "emulator-quickstart",
        "oauth-project-auth",
        "package-lifecycle",
        "homebrew-install-test",
        "malicious-extension",
        "malicious-import",
        "malicious-package",
    }),
}

_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_SOURCE_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_IDENTIFIER = re.compile(r"^[a-z][a-z0-9._-]{1,159}$")
_MODES = frozenset({"native", "geyser_emulated", "unsupported", "forbidden"})


class QualificationError(ValueError):
    """Evidence is incomplete, stale, mutable, or not canonically bound."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def bind_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    unsigned = dict(value)
    unsigned.pop("receipt_digest", None)
    return {**unsigned, "receipt_digest": digest(unsigned)}


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise QualificationError(f"{label} fields differ from the frozen receipt contract")


def validate_receipt(value: Mapping[str, Any], *, now: float | None = None) -> dict[str, Any]:
    receipt = dict(value)
    _exact_keys(receipt, {
        "schema_version", "receipt_kind", "subject", "layer", "suite_version",
        "cases", "assertions", "issued_at", "expires_at", "source_commit",
        "artifact_ref", "grants_authority", "security_warranty", "receipt_digest",
    }, "receipt")
    if receipt["schema_version"] != 1 or receipt["receipt_kind"] != "geyser_qualification":
        raise QualificationError("receipt schema or kind is unsupported")
    layer = str(receipt["layer"])
    if layer not in LAYERS:
        raise QualificationError("qualification layer is unknown")
    if receipt["grants_authority"] is not False or receipt["security_warranty"] is not False:
        raise QualificationError("a technical receipt cannot grant authority or warranty")
    if _SOURCE_COMMIT.fullmatch(str(receipt["source_commit"])) is None:
        raise QualificationError("source_commit is not an exact Git revision")
    if _DIGEST.fullmatch(str(receipt["artifact_ref"])) is None:
        raise QualificationError("artifact_ref must bind immutable bytes")
    issued_at = float(receipt["issued_at"])
    expires_at = float(receipt["expires_at"])
    if expires_at <= issued_at or expires_at <= float(time.time() if now is None else now):
        raise QualificationError("qualification receipt is expired or has invalid time bounds")

    subject = receipt["subject"]
    if not isinstance(subject, Mapping):
        raise QualificationError("subject must be an object")
    _exact_keys(dict(subject), {
        "kind", "name", "version", "digest", "framework", "backend", "provider",
        "model_profile_digest", "placement", "privacy_posture", "os", "architecture",
        "python_version",
    }, "subject")
    if subject["kind"] not in {"runtime_adapter", "developer_artifact"}:
        raise QualificationError("subject kind is unsupported")
    if _IDENTIFIER.fullmatch(str(subject["name"])) is None:
        raise QualificationError("subject name is invalid")
    if not str(subject["version"]):
        raise QualificationError("subject version is empty")
    for key in ("digest", "model_profile_digest"):
        if _DIGEST.fullmatch(str(subject[key])) is None:
            raise QualificationError(f"subject {key} is invalid")

    raw_cases = receipt["cases"]
    if not isinstance(raw_cases, list):
        raise QualificationError("cases must be a list")
    observed: set[str] = set()
    for case in raw_cases:
        if not isinstance(case, Mapping):
            raise QualificationError("case must be an object")
        _exact_keys(dict(case), {"case_id", "passed", "evidence_ref", "evidence_digest"}, "case")
        case_id = str(case["case_id"])
        if case_id in observed or case["passed"] is not True:
            raise QualificationError("qualification cases must be unique and passing")
        if not str(case["evidence_ref"]) or _DIGEST.fullmatch(str(case["evidence_digest"])) is None:
            raise QualificationError("qualification case evidence is incomplete")
        observed.add(case_id)
    if observed != REQUIRED_CASES[layer]:
        raise QualificationError("qualification case set is incomplete for its layer")

    raw_assertions = receipt["assertions"]
    if not isinstance(raw_assertions, list):
        raise QualificationError("assertions must be a list")
    capabilities: set[str] = set()
    for assertion in raw_assertions:
        if not isinstance(assertion, Mapping):
            raise QualificationError("assertion must be an object")
        _exact_keys(dict(assertion), {"capability", "mode", "case_ids"}, "assertion")
        capability = str(assertion["capability"])
        case_ids = assertion["case_ids"]
        if (
            _IDENTIFIER.fullmatch(capability) is None
            or capability in capabilities
            or assertion["mode"] not in _MODES
            or not isinstance(case_ids, list)
            or not case_ids
            or not set(map(str, case_ids)) <= observed
        ):
            raise QualificationError("capability assertion is not uniquely bound to passing cases")
        capabilities.add(capability)

    unsigned = dict(receipt)
    receipt_digest = str(unsigned.pop("receipt_digest"))
    if receipt_digest != digest(unsigned):
        raise QualificationError("receipt_digest does not bind the canonical receipt")
    return receipt


def capability_matrix(
    receipts: Iterable[Mapping[str, Any]], *, now: float | None = None,
) -> dict[str, Any]:
    checked = [validate_receipt(value, now=now) for value in receipts]
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for receipt in checked:
        subject = receipt["subject"]
        key = (
            str(subject["kind"]),
            str(subject["name"]),
            str(subject["version"]),
            str(subject["digest"]),
        )
        groups.setdefault(key, []).append(receipt)

    rows: list[dict[str, Any]] = []
    for key, evidence in sorted(groups.items()):
        layers = {str(item["layer"]): str(item["receipt_digest"]) for item in evidence}
        if len(layers) != len(evidence):
            raise QualificationError("subject has duplicate evidence for one layer")
        required_layers = (
            {"developer_artifact"}
            if key[0] == "developer_artifact"
            else LAYERS - {"developer_artifact"}
        )
        capabilities: dict[str, str] = {}
        for item in sorted(evidence, key=lambda value: str(value["layer"])):
            for assertion in item["assertions"]:
                capability = str(assertion["capability"])
                mode = str(assertion["mode"])
                prior = capabilities.setdefault(capability, mode)
                if prior != mode:
                    raise QualificationError("evidence layers disagree on capability mode")
        subject = evidence[0]["subject"]
        rows.append({
            "subject": dict(subject),
            "qualified": set(layers) == set(required_layers),
            "layers": dict(sorted(layers.items())),
            "capabilities": dict(sorted(capabilities.items())),
            "expires_at": min(float(item["expires_at"]) for item in evidence),
        })
    unsigned = {"schema_version": 1, "generated_from_evidence": True, "rows": rows}
    return {**unsigned, "matrix_digest": digest(unsigned)}


__all__ = [
    "LAYERS",
    "REQUIRED_CASES",
    "QualificationError",
    "bind_receipt",
    "canonical_bytes",
    "capability_matrix",
    "digest",
    "validate_receipt",
]
