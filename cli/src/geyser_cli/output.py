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
        print(
            json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
            flush=True,
        )
    elif isinstance(normalized, str):
        print(normalized)
    else:
        print(json.dumps(normalized, indent=2, sort_keys=True, ensure_ascii=False))


def _printable(value: str) -> str:
    # Server-supplied names must not carry terminal control sequences.
    return "".join(char if char.isprintable() else "?" for char in value)


def table(headers: list[str], rows: list[list[str]]) -> str:
    """Left-aligned plain-text columns for human-readable listings."""
    rows = [[_printable(cell) for cell in row] for row in rows]
    widths = [
        max(len(header), *(len(row[index]) for row in rows)) if rows else len(header)
        for index, header in enumerate(headers)
    ]
    lines = [headers, *rows]
    return "\n".join(
        "  ".join(cell.ljust(width) for cell, width in zip(line, widths, strict=True)).rstrip()
        for line in lines
    )


__all__ = ["emit", "serializable", "table"]
