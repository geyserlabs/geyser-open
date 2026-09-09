"""The executable public package contract shared by local and Agent runtimes."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .sandbox import run_handler
from .validation import validate_instance, validate_schema

EXECUTABLE_KINDS = {"tool", "connector", "evaluator"}


class ExecutableDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    name: str
    description: str = Field(min_length=1, max_length=1000)
    handler: str = Field(pattern=r"^[A-Za-z0-9_/-]+\.py:[A-Za-z_][A-Za-z0-9_]*$")
    effect_class: Literal["pure"]
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]


def descriptor(root: Path, manifest: dict[str, Any]) -> ExecutableDescriptor:
    kind = manifest.get("kind")
    if kind not in EXECUTABLE_KINDS:
        raise ValueError("package has no executable JSON handler")
    value = ExecutableDescriptor.model_validate_json((root / f"{kind}.json").read_text())
    if value.name != manifest["name"] or manifest.get("permissions"):
        raise ValueError(
            "pure executable identity must match and cannot request ambient permissions"
        )
    relative = Path(value.handler.split(":", 1)[0])
    if ".." in relative.parts or not (root / relative).is_file():
        raise ValueError("declared handler must exist inside the package")
    validate_schema(value.input_schema)
    validate_schema(value.output_schema)
    return value


def run_extension(
    root: Path, value: Any, *, timeout: float = 5.0, cancel_event: threading.Event | None = None
) -> Any:
    deadline = time.monotonic() + timeout
    if cancel_event is not None and cancel_event.is_set():
        raise ValueError("extension canceled")
    root = root.expanduser().resolve()
    manifest = json.loads((root / "geyser-package.json").read_text())
    definition = descriptor(root, manifest)
    try:
        validate_instance(
            definition.input_schema, value, deadline=deadline, cancel_event=cancel_event
        )
    except Exception as exc:
        raise ValueError("input_invalid") from exc
    result = run_handler(
        root,
        definition.handler,
        value,
        timeout=max(0.001, deadline - time.monotonic()),
        cancel_event=cancel_event,
    )
    try:
        validate_instance(
            definition.output_schema, result, deadline=deadline, cancel_event=cancel_event
        )
    except Exception as exc:
        raise ValueError("output_invalid") from exc
    return result
