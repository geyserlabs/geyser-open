"""Portable instructions and context applied to one qualified developer task.

The enclosing project package supplies publisher trust. This descriptor never
imports an account, grants a tool, changes shared settings, or restores a session.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

OVERLAY_KINDS = {"agent-bundle", "skill", "model-profile"}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class BundleSkill(StrictModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9-]{1,79}$")
    description: str = Field(min_length=1, max_length=1000)
    instructions: str = Field(min_length=1, max_length=32768)


class PortableContext(StrictModel):
    title: str = Field(min_length=1, max_length=160)
    source: str = Field(min_length=1, max_length=1000)
    kind: Literal["notes", "history", "memory"] = "notes"
    content: str = Field(min_length=1, max_length=32768)


class BundleReference(StrictModel):
    kind: Literal["history", "memory", "artifact", "deployment", "relationship"]
    ref: str = Field(min_length=1, max_length=1000)


class ModelSelection(StrictModel):
    schema_version: Literal[1] = 1
    model_ref: str = Field(default="", max_length=512)
    model_profile_digest: str = Field(default="", pattern=r"^(|sha256:[0-9a-f]{64})$")
    policy_ref: str = Field(default="", max_length=512)

    def require_current(self, current: dict[str, str]) -> None:
        for key, value in self.model_dump(exclude={"schema_version"}).items():
            if value and value != current.get(key, ""):
                raise ValueError("bundle_reference_unavailable")


class TaskBundle(StrictModel):
    schema_version: Literal[1] = 1
    name: str = Field(pattern=r"^[a-z][a-z0-9-]{1,79}$")
    persona: str = Field(default="", max_length=32768)
    skills: list[BundleSkill] = Field(default_factory=list, max_length=32)
    context: list[PortableContext] = Field(default_factory=list, max_length=32)
    selection: ModelSelection = Field(default_factory=ModelSelection)
    references: list[BundleReference] = Field(default_factory=list, max_length=32)

    @model_validator(mode="after")
    def bounded_unique_contents(self) -> TaskBundle:
        if len({skill.name for skill in self.skills}) != len(self.skills):
            raise ValueError("bundle skill names must be unique")
        if len(self.model_dump_json().encode("utf-8")) > 128 * 1024:
            raise ValueError("bundle instructions and context exceed 128 KiB")
        return self


def overlay_descriptor(root: Path, manifest: dict[str, Any]) -> TaskBundle:
    """Validate text-only packages without reading or executing external content."""
    if manifest.get("permissions"):
        raise ValueError("instruction packages cannot request ambient permissions")
    kind = manifest.get("kind")
    name = manifest["name"]
    if kind == "agent-bundle":
        value = TaskBundle.model_validate_json((root / "agent-bundle.json").read_text())
        if value.name != name:
            raise ValueError("bundle identity must match its package")
        return value
    if kind == "skill":
        return TaskBundle(
            name=name,
            skills=[
                BundleSkill(
                    name=name,
                    description=f"Project procedure: {name}",
                    instructions=(root / "SKILL.md").read_text(),
                )
            ],
        )
    if kind == "model-profile":
        selection = ModelSelection.model_validate_json((root / "model-profile.json").read_text())
        if not selection.model_ref or not selection.model_profile_digest:
            raise ValueError("model profiles require an exact model and qualified profile digest")
        return TaskBundle(name=name, selection=selection)
    raise ValueError("package does not contain task instructions")


def overlay_preview(bundle: TaskBundle, current: dict[str, str]) -> dict[str, Any]:
    """Resolve a bundle against the current binding; references remain explicit omissions."""
    bundle.selection.require_current(current)

    def digest(value: Any) -> str:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return "sha256:" + hashlib.sha256(encoded.encode()).hexdigest()

    applied = []
    if bundle.persona:
        applied.append({"kind": "persona", "name": bundle.name, "digest": digest(bundle.persona)})
    applied.extend(
        {"kind": "skill", "name": item.name, "digest": digest(item.model_dump())}
        for item in bundle.skills
    )
    applied.extend(
        {"kind": "context", "name": item.title, "digest": digest(item.model_dump())}
        for item in bundle.context
    )
    return {
        "applied": applied,
        "selection": bundle.selection.model_dump(exclude_defaults=True),
        "omitted": [
            {**item.model_dump(), "reason": "reference_only_not_restored"}
            for item in bundle.references
        ],
        "shared_settings_changed": False,
        "permissions_granted": [],
    }
