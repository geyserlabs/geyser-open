"""Safe extension scaffolds used by ``geyser init``."""

from __future__ import annotations

import json
import re
from pathlib import Path

KINDS = ("skill", "connector", "tool", "evaluator", "model-profile", "agent-bundle")
_NAME = re.compile(r"^[a-z][a-z0-9-]{1,63}$")


def _json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def scaffold_files(kind: str, name: str) -> dict[str, str]:
    common = {
        "geyser-package.json": _json({
            "schema_version": 1,
            "kind": kind,
            "name": name,
            "version": "0.1.0",
            "permissions": [],
        }),
        "README.md": (
            f"# {name}\n\nA credential-free `{kind}` extension for Geyser Open. "
            "Declared permissions do not grant authority; server policy remains authoritative.\n"
        ),
        "evals/cases.json": _json({
            "schema_version": 1,
            "frozen": True,
            "cases": [
                {"case_id": "bounded-success-1", "critical": False, "expected": "success"},
                {
                    "case_id": "critical-denial-1",
                    "critical": True,
                    "expected": "deny_without_explicit_authority",
                },
            ],
        }),
    }
    if kind == "skill":
        return {**common, "SKILL.md": (
            f"# {name}\n\n## Purpose\n\nDescribe one bounded capability.\n\n"
            "## Authority\n\nThis skill never grants tools, credentials, or approval.\n"
        )}
    if kind == "connector":
        return {**common, "connector.json": _json({
            "schema_version": 1,
            "connector_id": name,
            "directions": ["inbound"],
            "identity_link_required": True,
            "content_storage": "customer_cell_reference_only",
            "delivery": {"deduplicate": True, "max_loop_hops": 8},
            "permissions": {"event_types": [], "network_origins": []},
            "revocable": True,
        })}
    if kind == "tool":
        return {**common, "tool.json": _json({
            "schema_version": 1,
            "tool_name": name,
            "description": "Describe the bounded effect without promising authority.",
            "input_schema": {"type": "object", "additionalProperties": False},
            "effect_class": "read_only",
            "approval_posture": "policy_decides",
            "idempotency_required": True,
        })}
    if kind == "evaluator":
        return {**common, "evaluator.json": _json({
            "schema_version": 1,
            "evaluator_id": name,
            "score_range": [0, 1],
            "critical_slices": ["authorization", "privacy", "false_success"],
            "content_capture": False,
        })}
    if kind == "model-profile":
        return {**common, "model-profile.json": _json({
            "schema_version": 1,
            "profile_id": name,
            "qualified": False,
            "qualification_ref": "",
            "custody": "declare-before-use",
            "fallback": "none",
            "task_performance_cards": {},
        })}
    return {**common, "agent-bundle-selection.json": _json({
        "schema_version": 1,
        "name": name,
        "components": [
            "identity_persona",
            "skills",
            "policy_references",
            "brain_export",
            "history_index",
            "artifact_manifest",
        ],
        "owner_review_required": True,
        "include_credentials": False,
        "include_provider_sessions": False,
        "include_hidden_reasoning": False,
    })}


def scaffold(kind: str, name: str, output: Path) -> Path:
    if kind not in KINDS:
        raise ValueError("unknown scaffold kind")
    if _NAME.fullmatch(name) is None:
        raise ValueError("name must be 2-64 lowercase letters, numbers, and hyphens")
    root = output.expanduser().resolve() / name
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty scaffold: {root}")
    for relative, body in scaffold_files(kind, name).items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    return root


__all__ = ["KINDS", "scaffold", "scaffold_files"]
