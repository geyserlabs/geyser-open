from __future__ import annotations

from copy import deepcopy

import pytest

from conformance.qualification import (
    LAYERS,
    REQUIRED_CASES,
    QualificationError,
    bind_receipt,
    capability_matrix,
    digest,
    validate_receipt,
)


def _receipt(layer: str, *, kind: str = "runtime_adapter") -> dict:
    subject = {
        "kind": kind,
        "name": "geyser.open" if kind == "runtime_adapter" else "geyser.cli",
        "version": "0.1.0b3",
        "digest": digest({"kind": kind}),
        "framework": "open" if kind == "runtime_adapter" else "",
        "backend": "pydantic-ai-harness" if kind == "runtime_adapter" else "",
        "provider": "deterministic" if kind == "runtime_adapter" else "",
        "model_profile_digest": digest({"model": kind}),
        "placement": "linux-amd64",
        "privacy_posture": "local-emulator" if kind == "developer_artifact" else "private",
        "os": "ubuntu-24.04",
        "architecture": "amd64",
        "python_version": "3.11",
    }
    cases = [{
        "case_id": case_id,
        "passed": True,
        "evidence_ref": f"pytest:{case_id}",
        "evidence_digest": digest({"case": case_id}),
    } for case_id in sorted(REQUIRED_CASES[layer])]
    assertion_case = cases[0]["case_id"]
    value = {
        "schema_version": 1,
        "receipt_kind": "geyser_qualification",
        "subject": subject,
        "layer": layer,
        "suite_version": "geyser-universal-conformance-v1",
        "cases": cases,
        "assertions": [{
            "capability": f"{layer}.verified",
            "mode": "geyser_emulated" if kind == "developer_artifact" else "native",
            "case_ids": [assertion_case],
        }],
        "issued_at": 1000.0,
        "expires_at": 2000.0,
        "source_commit": "a" * 40,
        "artifact_ref": digest({"artifact": kind}),
        "grants_authority": False,
        "security_warranty": False,
    }
    return bind_receipt(value)


def test_complete_receipt_binds_exact_cases_bytes_and_environment() -> None:
    value = _receipt("runtime_adapter")
    assert validate_receipt(value, now=1500) == value
    assert value["subject"]["architecture"] == "amd64"
    assert value["subject"]["python_version"] == "3.11"


@pytest.mark.parametrize("mutation", ["expired", "failed", "missing", "tampered", "authority"])
def test_receipts_fail_closed(mutation: str) -> None:
    value = _receipt("protocol_core")
    now = 1500.0
    if mutation == "expired":
        now = 2000.0
    elif mutation == "failed":
        value["cases"][0]["passed"] = False
        value = bind_receipt(value)
    elif mutation == "missing":
        value["cases"].pop()
        value = bind_receipt(value)
    elif mutation == "tampered":
        value["subject"]["version"] = "9.9.9"
    else:
        value["grants_authority"] = True
        value = bind_receipt(value)
    with pytest.raises(QualificationError):
        validate_receipt(value, now=now)


def test_matrix_is_generated_only_from_complete_non_conflicting_evidence() -> None:
    runtime = [_receipt(layer) for layer in sorted(LAYERS - {"developer_artifact"})]
    developer = [_receipt("developer_artifact", kind="developer_artifact")]
    matrix = capability_matrix([*runtime, *developer], now=1500)
    assert matrix["generated_from_evidence"] is True
    assert len(matrix["rows"]) == 2
    assert all(row["qualified"] is True for row in matrix["rows"])
    assert matrix["matrix_digest"].startswith("sha256:")

    partial = capability_matrix(runtime[:-1], now=1500)
    assert partial["rows"][0]["qualified"] is False

    conflicting = deepcopy(runtime)
    conflicting[1]["assertions"][0]["capability"] = conflicting[0]["assertions"][0]["capability"]
    conflicting[1]["assertions"][0]["mode"] = "unsupported"
    conflicting[1] = bind_receipt(conflicting[1])
    with pytest.raises(QualificationError, match="disagree"):
        capability_matrix(conflicting, now=1500)
