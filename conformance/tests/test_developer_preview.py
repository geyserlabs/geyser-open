from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from conformance.developer_preview import PREVIEW_STEPS, validate_preview_receipt
from conformance.qualification import QualificationError, bind_receipt, digest


def _receipt() -> dict:
    return bind_receipt({
        "schema_version": 1,
        "receipt_kind": "geyser_external_developer_preview",
        "participant": {
            "identity_digest": digest({"participant": "external"}),
            "was_implementer": False,
            "private_help_used": False,
        },
        "environment": {
            "machine_identity_digest": digest({"machine": "clean"}),
            "os": "ubuntu-24.04",
            "architecture": "amd64",
            "python_version": "3.12",
            "clean_machine": True,
            "customer_id": 1,
            "sandbox_ref_digest": digest({"sandbox": "customer-1"}),
        },
        "release": {
            "version": "0.1.0b1",
            "source_commit": "a" * 40,
            "sdk_artifact_digest": digest({"artifact": "sdk"}),
            "cli_artifact_digest": digest({"artifact": "cli"}),
            "docs_url": "https://docs.geyserlabs.ai/0.1.0b1/",
            "sdk_package_url": "https://pypi.org/project/geyser-sdk/0.1.0b1/",
            "cli_package_url": "https://pypi.org/project/geyser-open/0.1.0b1/",
            "github_release_url": (
                "https://github.com/geyserlabs/geyser-open/releases/tag/v0.1.0b1"
            ),
        },
        "steps": [{
            "step_id": step_id,
            "passed": True,
            "evidence_ref": f"external-preview:{step_id}",
            "evidence_digest": digest({"step": step_id}),
        } for step_id in PREVIEW_STEPS],
        "defects": [{
            "defect_id": "docs-1",
            "summary_digest": digest({"summary": "confusing step"}),
            "regression_ref": "tests:test_docs_regression",
            "resolved": True,
        }],
        "started_at": 1000.0,
        "completed_at": 2000.0,
        "cleanup": {
            "credential_revoked": True,
            "sandbox_artifacts_removed": True,
            "local_artifacts_removed": True,
            "canary_removed": True,
            "browser_session_closed": True,
        },
        "grants_authority": False,
        "security_warranty": False,
    })


def test_complete_independent_preview_receipt_is_bound() -> None:
    value = _receipt()
    assert validate_preview_receipt(value) == value


def test_public_preview_template_freezes_the_exact_path() -> None:
    path = Path(__file__).parents[1] / "fixtures" / "external-preview-receipt.template.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    assert "receipt_digest" not in value
    assert tuple(step["step_id"] for step in value["steps"]) == PREVIEW_STEPS
    assert value["participant"]["was_implementer"] is False
    assert value["environment"]["customer_id"] == 1


@pytest.mark.parametrize("mutation", [
    "implementer",
    "private-help",
    "non-customer-1",
    "unclean-host",
    "missing-step",
    "failed-step",
    "open-defect",
    "cleanup",
    "tamper",
])
def test_incomplete_external_preview_fails_closed(mutation: str) -> None:
    value = deepcopy(_receipt())
    if mutation == "implementer":
        value["participant"]["was_implementer"] = True
    elif mutation == "private-help":
        value["participant"]["private_help_used"] = True
    elif mutation == "non-customer-1":
        value["environment"]["customer_id"] = 2
    elif mutation == "unclean-host":
        value["environment"]["clean_machine"] = False
    elif mutation == "missing-step":
        value["steps"].pop()
    elif mutation == "failed-step":
        value["steps"][0]["passed"] = False
    elif mutation == "open-defect":
        value["defects"][0]["resolved"] = False
    elif mutation == "cleanup":
        value["cleanup"]["credential_revoked"] = False
    else:
        value["release"]["version"] = "9.9.9"
        with pytest.raises(QualificationError, match="does not bind"):
            validate_preview_receipt(value)
        return
    value = bind_receipt(value)
    with pytest.raises(QualificationError):
        validate_preview_receipt(value)
