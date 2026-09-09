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
        "geyser-package.json": _json(
            {
                "schema_version": 1,
                "kind": kind,
                "name": name,
                "version": "0.1.0",
                "permissions": [],
            }
        ),
        "README.md": (
            f"# {name}\n\nA credential-free `{kind}` extension for Geyser Open. "
            "Declared permissions do not grant authority; server policy remains authoritative.\n"
        ),
        "evals/cases.json": _json(
            {
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
            }
        ),
    }
    if kind in {"tool", "connector", "evaluator"}:
        output_schema = {
            "type": "object",
            "required": ["word_count"],
            "properties": {"word_count": {"type": "integer", "minimum": 0}},
            "additionalProperties": False,
        }
        common["README.md"] += (
            "\nThis example counts words in supplied text. "
            "It runs as a pure JSON handler in an OS sandbox. "
            "No host files, network, subprocesses, or credentials are available.\n\n"
            "Run `geyser test .` to execute the frozen examples, "
            "`geyser dev .` to invoke the handler, "
            "and `geyser package .` to build an immutable archive.\n"
        )
        common["evals/cases.json"] = _json(
            {
                "schema_version": 1,
                "frozen": True,
                "cases": [
                    {
                        "case_id": "word-count",
                        "input": {"text": "hello world"},
                        "expected_output": {"word_count": 2},
                        "critical": False,
                    },
                    {
                        "case_id": "reject-url-as-authority",
                        "input": {"url": "https://example.invalid"},
                        "expected_error": "input_invalid",
                        "critical": True,
                    },
                ],
            }
        )
        return {
            **common,
            f"{kind}.json": _json(
                {
                    "schema_version": 1,
                    "name": name,
                    "description": "Count words in supplied text without external access.",
                    "handler": "handler.py:run",
                    "effect_class": "pure",
                    "input_schema": {
                        "type": "object",
                        "required": ["text"],
                        "properties": {"text": {"type": "string", "maxLength": 10000}},
                        "additionalProperties": False,
                    },
                    "output_schema": output_schema,
                }
            ),
            "handler.py": (
                'def run(value):\n    return {"word_count": len(value["text"].split())}\n'
            ),
        }
    if kind == "skill":
        return {
            **common,
            "SKILL.md": (
                f"# {name}\n\n## Purpose\n\nDescribe one bounded capability.\n\n"
                "## Authority\n\nThis skill never grants tools, credentials, or approval.\n"
            ),
        }
    if kind == "model-profile":
        return {
            **common,
            "model-profile.json": _json(
                {
                    "schema_version": 1,
                    "profile_id": name,
                    "qualified": False,
                    "qualification_ref": "",
                    "custody": "declare-before-use",
                    "fallback": "none",
                    "task_performance_cards": {},
                }
            ),
        }
    return {
        **common,
        "agent-bundle-selection.json": _json(
            {
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
            }
        ),
    }


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
