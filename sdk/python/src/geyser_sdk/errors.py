from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Problem:
    type: str
    title: str
    status: int
    detail: str
    code: str
    instance: str = ""
    request_id: str = ""
    current_version: int | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any], status: int) -> Problem:
        error = value.get("error")
        if isinstance(error, Mapping) and "code" not in value:
            return cls._from_compatible_error(error, status)
        current = value.get("current_version")
        return cls(
            type=str(value.get("type") or "about:blank"),
            title=str(value.get("title") or "Geyser request failed"),
            status=int(value.get("status") or status),
            detail=str(value.get("detail") or "The request was rejected."),
            code=str(value.get("code") or "request_failed"),
            instance=str(value.get("instance") or ""),
            request_id=str(value.get("request_id") or ""),
            current_version=int(current) if isinstance(current, int) else None,
        )

    @classmethod
    def _from_compatible_error(cls, error: Mapping[str, Any], status: int) -> Problem:
        # OpenAI-compatible routes return {"error": {"message", "type", "code"}};
        # the Anthropic-compatible route returns {"type": "error", "error": {"type", "message"}}.
        kind = str(error.get("type") or "")
        return cls(
            type="about:blank",
            title=kind or "Geyser request failed",
            status=status,
            detail=str(error.get("message") or "The request was rejected."),
            code=str(error.get("code") or kind or "request_failed"),
        )


class GeyserError(RuntimeError):
    """Base exception for SDK transport and contract failures."""


class ProblemError(GeyserError):
    def __init__(self, problem: Problem) -> None:
        self.problem = problem
        super().__init__(f"{problem.code} ({problem.status}): {problem.detail}")


class TransportError(GeyserError):
    """The server could not be reached after the safe retry policy."""


class ResponseValidationError(GeyserError):
    """The server response did not satisfy the public SDK contract."""
