"""Stable human and machine-readable command output."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel


def serializable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: serializable(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [serializable(child) for child in value]
    return value


def emit(value: Any, *, machine: bool) -> None:
    normalized = serializable(value)
    if machine:
        print(json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    elif isinstance(normalized, str):
        print(normalized)
    else:
        print(json.dumps(normalized, indent=2, sort_keys=True, ensure_ascii=False))


__all__ = ["emit", "serializable"]
