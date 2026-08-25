"""Independent external-developer preview receipt contract."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .qualification import QualificationError, bind_receipt, digest

PREVIEW_STEPS = (
    "discover-developer-page",
    "clean-install-canonical-channels",
    "run-emulator-quickstart",
    "scaffold-tool-or-skill",
    "add-frozen-success-and-denial",
    "authenticate-customer-1-sandbox",
    "stage-canary-signed-bytes",
    "inspect-durable-run-and-trace",
    "handle-approval-and-denial",
    "cleanup-and-report-friction",
)

_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise QualificationError(f"{label} differs from the frozen preview contract")


def _require_digest(value: Any, label: str) -> str:
    text = str(value)
    if _DIGEST.fullmatch(text) is None:
        raise QualificationError(f"{label} must be a sha256 digest")
    return text


def validate_preview_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    """Accept only an independent, complete, cleaned-up public preview run."""
    receipt = dict(value)
    _exact_keys(receipt, {
        "schema_version",
        "receipt_kind",
        "participant",
        "environment",
        "release",
        "steps",
        "defects",
        "started_at",
        "completed_at",
        "cleanup",
        "grants_authority",
        "security_warranty",
        "receipt_digest",
    }, "preview receipt")
    if receipt["schema_version"] != 1 or receipt["receipt_kind"] != (
        "geyser_external_developer_preview"
    ):
        raise QualificationError("preview receipt schema or kind is unsupported")
    if receipt["grants_authority"] is not False or receipt["security_warranty"] is not False:
        raise QualificationError("a preview receipt cannot grant authority or warranty")

    participant = receipt["participant"]
    if not isinstance(participant, Mapping):
        raise QualificationError("participant must be an object")
    _exact_keys(dict(participant), {
        "identity_digest", "was_implementer", "private_help_used",
    }, "participant")
    _require_digest(participant["identity_digest"], "participant identity")
    if participant["was_implementer"] is not False or participant["private_help_used"] is not False:
        raise QualificationError("the preview must be independent and use no private help")

    environment = receipt["environment"]
    if not isinstance(environment, Mapping):
        raise QualificationError("environment must be an object")
    _exact_keys(dict(environment), {
        "machine_identity_digest", "os", "architecture", "python_version",
        "clean_machine", "customer_id", "sandbox_ref_digest",
    }, "environment")
    _require_digest(environment["machine_identity_digest"], "machine identity")
    _require_digest(environment["sandbox_ref_digest"], "sandbox reference")
    if environment["os"] not in {"macos", "ubuntu-24.04"}:
        raise QualificationError("preview OS is not a supported clean-host target")
    if environment["architecture"] not in {"arm64", "amd64"}:
        raise QualificationError("preview architecture is unsupported")
    if str(environment["python_version"]) not in {"3.11", "3.12", "3.13"}:
        raise QualificationError("preview Python version is unsupported")
    if environment["clean_machine"] is not True or environment["customer_id"] != 1:
        raise QualificationError("preview must use a clean host and customer 1 sandbox")

    release = receipt["release"]
    if not isinstance(release, Mapping):
        raise QualificationError("release must be an object")
    _exact_keys(dict(release), {
        "version", "source_commit", "sdk_artifact_digest", "cli_artifact_digest",
        "docs_url", "sdk_package_url", "cli_package_url", "github_release_url",
    }, "release")
    if not str(release["version"]) or _COMMIT.fullmatch(str(release["source_commit"])) is None:
        raise QualificationError("release version or source commit is invalid")
    _require_digest(release["sdk_artifact_digest"], "SDK artifact")
    _require_digest(release["cli_artifact_digest"], "CLI artifact")
    for key in ("docs_url", "sdk_package_url", "cli_package_url", "github_release_url"):
        if not str(release[key]).startswith("https://"):
            raise QualificationError(f"release {key} must be a canonical HTTPS URL")

    steps = receipt["steps"]
    if not isinstance(steps, list):
        raise QualificationError("preview steps must be a list")
    observed: list[str] = []
    for raw in steps:
        if not isinstance(raw, Mapping):
            raise QualificationError("preview step must be an object")
        step = dict(raw)
        _exact_keys(step, {"step_id", "passed", "evidence_ref", "evidence_digest"}, "step")
        observed.append(str(step["step_id"]))
        if step["passed"] is not True or not str(step["evidence_ref"]):
            raise QualificationError("every preview step needs passing evidence")
        _require_digest(step["evidence_digest"], "step evidence")
    if tuple(observed) != PREVIEW_STEPS:
        raise QualificationError("preview steps are missing, duplicated, or out of order")

    defects = receipt["defects"]
    if not isinstance(defects, list):
        raise QualificationError("defects must be a list")
    defect_ids: set[str] = set()
    for raw in defects:
        if not isinstance(raw, Mapping):
            raise QualificationError("defect must be an object")
        defect = dict(raw)
        _exact_keys(defect, {
            "defect_id", "summary_digest", "regression_ref", "resolved",
        }, "defect")
        defect_id = str(defect["defect_id"])
        if (
            not defect_id
            or defect_id in defect_ids
            or not str(defect["regression_ref"])
            or defect["resolved"] is not True
        ):
            raise QualificationError("every preview defect needs a closed regression")
        defect_ids.add(defect_id)
        _require_digest(defect["summary_digest"], "defect summary")

    started_at = float(receipt["started_at"])
    completed_at = float(receipt["completed_at"])
    if started_at <= 0 or completed_at <= started_at:
        raise QualificationError("preview timestamps are invalid")
    cleanup = receipt["cleanup"]
    if not isinstance(cleanup, Mapping):
        raise QualificationError("cleanup must be an object")
    _exact_keys(dict(cleanup), {
        "credential_revoked", "sandbox_artifacts_removed", "local_artifacts_removed",
        "canary_removed", "browser_session_closed",
    }, "cleanup")
    if any(item is not True for item in cleanup.values()):
        raise QualificationError("preview cleanup is incomplete")

    unsigned = dict(receipt)
    claimed = str(unsigned.pop("receipt_digest"))
    if claimed != digest(unsigned):
        raise QualificationError("receipt_digest does not bind the preview receipt")
    return receipt


__all__ = [
    "PREVIEW_STEPS",
    "bind_receipt",
    "validate_preview_receipt",
]
