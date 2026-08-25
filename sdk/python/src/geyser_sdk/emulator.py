"""Deterministic, credential-free local emulator for durable-run semantics."""

from __future__ import annotations

import copy
import hashlib
import inspect
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from ._json import bytes_digest, digest
from .errors import GeyserError
from .models import TypedTask
from .structured_outcomes import normalize_contract, validate_outcome


class EmulatorError(GeyserError):
    """A deterministic emulator invariant failed."""


@dataclass(slots=True)
class LocalEmulator:
    """Single-tenant emulator with durable-event crash injection and no I/O."""

    crash_after: set[str] = field(default_factory=set)
    events: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    idempotency: dict[tuple[str, str], str] = field(default_factory=dict)
    checkpoints: dict[str, bytes] = field(default_factory=dict)
    approvals: dict[str, dict[str, Any]] = field(default_factory=dict)
    models: dict[str, Callable[[TypedTask], Any | Awaitable[Any]]] = field(default_factory=dict)
    tools: dict[
        str, Callable[[Mapping[str, Any]], Any | Awaitable[Any]]
    ] = field(default_factory=dict)
    model_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)

    def admit(self, run_id: str, task: TypedTask) -> dict[str, Any]:
        if run_id in self.events:
            return self.project(run_id)
        task_data = task.model_dump(exclude={"outcome_contract"})
        self.events[run_id] = [{
            "sequence": 1,
            "event_type": "run.admitted",
            "data": task_data,
            "digest": digest(task.model_dump()),
        }]
        return self.project(run_id)

    def append(
        self,
        run_id: str,
        *,
        event_type: str,
        key: str,
        expected_sequence: int,
        data: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        rows = self.events.get(run_id)
        if rows is None:
            raise EmulatorError("unknown emulator run")
        payload = dict(data or {})
        event_digest = digest({"event_type": event_type, "data": payload})
        identity = (run_id, key)
        if identity in self.idempotency:
            if self.idempotency[identity] != event_digest:
                raise EmulatorError("emulator idempotency key was reused")
            return self.project(run_id)
        if expected_sequence != len(rows):
            raise EmulatorError("emulator sequence conflict")
        rows.append({
            "sequence": len(rows) + 1,
            "event_type": event_type,
            "data": payload,
            "digest": event_digest,
        })
        self.idempotency[identity] = event_digest
        if event_type in self.crash_after:
            raise EmulatorError(f"injected crash after durable {event_type}")
        return self.project(run_id)

    def checkpoint(self, run_id: str, payload: bytes) -> dict[str, Any]:
        if run_id not in self.events:
            raise EmulatorError("unknown emulator run")
        self.checkpoints[run_id] = bytes(payload)
        return {
            "checkpoint_ref": f"emulator-checkpoint:{run_id}",
            "checkpoint_digest": bytes_digest(payload),
            "size_bytes": len(payload),
        }

    def request_approval(
        self, run_id: str, *, approval_id: str, binding: Mapping[str, Any]
    ) -> dict[str, Any]:
        if run_id not in self.events:
            raise EmulatorError("unknown emulator run")
        if approval_id in self.approvals:
            raise EmulatorError("approval already exists")
        value = {
            "run_id": run_id,
            "approval_id": approval_id,
            "binding_digest": digest(binding),
            "state": "requested",
            "version": 1,
        }
        self.approvals[approval_id] = value
        return copy.deepcopy(value)

    def decide_approval(
        self, approval_id: str, *, binding_digest: str, approve: bool
    ) -> dict[str, Any]:
        value = self.approvals.get(approval_id)
        if value is None or value["state"] != "requested":
            raise EmulatorError("approval is missing or already decided")
        if value["binding_digest"] != binding_digest:
            raise EmulatorError("approval binding is stale")
        value.update({"state": "approved" if approve else "rejected", "version": 2})
        return copy.deepcopy(value)

    def validate_result(self, task: TypedTask, value: Any) -> Any:
        contract = normalize_contract(task.outcome_contract)
        return value if contract is None else validate_outcome(contract, value)

    def register_model(
        self, model_ref: str, implementation: Callable[[TypedTask], Any | Awaitable[Any]]
    ) -> None:
        if not model_ref or model_ref in self.models:
            raise EmulatorError("emulator model ref is empty or already registered")
        self.models[model_ref] = implementation

    def register_tool(
        self,
        tool_name: str,
        implementation: Callable[[Mapping[str, Any]], Any | Awaitable[Any]],
    ) -> None:
        if not tool_name or tool_name in self.tools:
            raise EmulatorError("emulator tool name is empty or already registered")
        self.tools[tool_name] = implementation

    async def call_model(self, run_id: str, task: TypedTask) -> Any:
        implementation = self.models.get(task.model_ref)
        if implementation is None:
            raise EmulatorError("emulator model is not registered")
        self.append(
            run_id,
            event_type="model.requested",
            key=f"model:{len(self.model_calls)}:requested",
            expected_sequence=self.project(run_id)["sequence"],
            data={"model_ref": task.model_ref},
        )
        result = implementation(task)
        if inspect.isawaitable(result):
            result = await result
        result = self.validate_result(task, result)
        call = {
            "run_id": run_id,
            "model_ref": task.model_ref,
            "result_digest": digest(result),
        }
        self.model_calls.append(call)
        self.append(
            run_id,
            event_type="model.output_committed",
            key=f"model:{len(self.model_calls) - 1}:committed",
            expected_sequence=self.project(run_id)["sequence"],
            data=call,
        )
        return result

    async def call_tool(
        self,
        run_id: str,
        *,
        tool_name: str,
        arguments: Mapping[str, Any],
        approval_id: str = "",
    ) -> Any:
        implementation = self.tools.get(tool_name)
        if implementation is None:
            raise EmulatorError("emulator tool is not registered")
        arguments_digest = digest(arguments)
        if approval_id:
            approval = self.approvals.get(approval_id)
            binding = {
                "run_id": run_id,
                "tool_name": tool_name,
                "arguments_digest": arguments_digest,
            }
            if approval is None or approval.get("state") != "approved":
                raise EmulatorError("tool approval is not approved")
            if approval.get("binding_digest") != digest(binding):
                raise EmulatorError("tool approval does not bind this invocation")
        effect_id = "eff_" + hashlib.sha256(
            f"{run_id}\0{tool_name}\0{arguments_digest}".encode()
        ).hexdigest()[:40]
        index = len(self.tool_calls)
        self.append(
            run_id,
            event_type="tool.started",
            key=f"tool:{index}:started",
            expected_sequence=self.project(run_id)["sequence"],
            data={
                "effect_id": effect_id,
                "tool_name": tool_name,
                "arguments_digest": arguments_digest,
            },
        )
        result = implementation(dict(arguments))
        if inspect.isawaitable(result):
            result = await result
        call = {
            "run_id": run_id,
            "effect_id": effect_id,
            "tool_name": tool_name,
            "arguments_digest": arguments_digest,
            "result_digest": digest(result),
        }
        self.tool_calls.append(call)
        self.append(
            run_id,
            event_type="tool.completed",
            key=f"tool:{index}:completed",
            expected_sequence=self.project(run_id)["sequence"],
            data=call,
        )
        return result

    def project(self, run_id: str) -> dict[str, Any]:
        rows = self.events.get(run_id)
        if rows is None:
            raise EmulatorError("unknown emulator run")
        state = "admitted"
        for row in rows[1:]:
            state = {
                "run.started": "running",
                "run.paused": "paused",
                "run.resumed": "running",
                "run.completed": "completed",
                "run.failed": "failed",
                "run.canceled": "canceled",
            }.get(row["event_type"], state)
        return {
            "run_id": run_id,
            "state": state,
            "sequence": len(rows),
            "events": copy.deepcopy(rows),
            "checkpoint_digest": (
                bytes_digest(self.checkpoints[run_id]) if run_id in self.checkpoints else ""
            ),
        }


__all__ = ["EmulatorError", "LocalEmulator"]
