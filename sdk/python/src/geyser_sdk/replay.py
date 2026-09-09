"""Bounded explicit tool replies for a replay that never invokes live tools."""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .validation import validate_schema


class StubTool(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str = Field(pattern=r"^[A-Za-z_][A-Za-z0-9_]{0,159}$")
    description: str = Field(min_length=1, max_length=1000)
    parameters: dict[str, Any]


class StubReply(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    tool_name: str
    args_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    result: Any


class ToolStubs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1] = 1
    tools: list[StubTool] = Field(min_length=1, max_length=32)
    replies: list[StubReply] = Field(default_factory=list, max_length=128)

    @model_validator(mode="after")
    def bounded_exact_replies(self) -> ToolStubs:
        if len(json.dumps(self.model_dump(), allow_nan=False).encode()) > 256 * 1024:
            raise ValueError("tool stubs exceed 256 KiB")
        names = {tool.name for tool in self.tools}
        if len(names) != len(self.tools):
            raise ValueError("stub tool names must be unique")
        if any(reply.tool_name not in names for reply in self.replies):
            raise ValueError("every stub reply must name a declared tool")
        if len({(reply.tool_name, reply.args_digest) for reply in self.replies}) != len(
            self.replies
        ):
            raise ValueError("stub replies must have unique argument bindings")
        for tool in self.tools:
            if tool.parameters.get("type") != "object":
                raise ValueError("stub tool parameters must be an object schema")
            validate_schema(tool.parameters)
        return self
