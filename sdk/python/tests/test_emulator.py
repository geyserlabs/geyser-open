from __future__ import annotations

import pytest
from geyser_sdk import EmulatorError, LocalEmulator, TypedTask, digest

SHA = "sha256:" + "a" * 64


def task() -> TypedTask:
    return TypedTask(
        task_id="task-1",
        context_id="context-1",
        prompt_digest=SHA,
        model_ref="deterministic:answer",
        outcome_contract={
            "schema_version": 1,
            "schema_ref": "example:answer:v1",
            "json_schema": {
                "type": "object",
                "properties": {"answer": {"type": "string"}},
                "required": ["answer"],
                "additionalProperties": False,
            },
        },
    )


def test_durable_crash_and_idempotent_recovery() -> None:
    emulator = LocalEmulator(crash_after={"run.started"})
    emulator.admit("run-1", task())
    with pytest.raises(EmulatorError, match="injected crash"):
        emulator.append(
            "run-1", event_type="run.started", key="start", expected_sequence=1
        )
    assert emulator.project("run-1")["sequence"] == 2
    recovered = emulator.append(
        "run-1", event_type="run.started", key="start", expected_sequence=1
    )
    assert recovered["sequence"] == 2
    with pytest.raises(EmulatorError, match="reused"):
        emulator.append(
            "run-1",
            event_type="run.started",
            key="start",
            expected_sequence=2,
            data={"drift": True},
        )
    with pytest.raises(EmulatorError, match="sequence conflict"):
        emulator.append("run-1", event_type="run.completed", key="done", expected_sequence=9)


@pytest.mark.asyncio
async def test_models_tools_approvals_and_checkpoints() -> None:
    emulator = LocalEmulator()
    current = task()
    emulator.admit("run-1", current)
    emulator.register_model("deterministic:answer", lambda _task: {"answer": "42"})
    emulator.register_tool("store", lambda arguments: {"stored": arguments["value"]})
    assert (await emulator.call_model("run-1", current)) == {"answer": "42"}
    binding = {
        "run_id": "run-1",
        "tool_name": "store",
        "arguments_digest": digest({"value": 42}),
    }
    approval = emulator.request_approval("run-1", approval_id="approval-1", binding=binding)
    with pytest.raises(EmulatorError, match="not approved"):
        await emulator.call_tool(
            "run-1",
            tool_name="store",
            arguments={"value": 42},
            approval_id="approval-1",
        )
    with pytest.raises(EmulatorError, match="stale"):
        emulator.decide_approval("approval-1", binding_digest=SHA, approve=True)
    emulator.decide_approval(
        "approval-1", binding_digest=approval["binding_digest"], approve=True
    )
    assert await emulator.call_tool(
        "run-1", tool_name="store", arguments={"value": 42}, approval_id="approval-1"
    ) == {"stored": 42}
    checkpoint = emulator.checkpoint("run-1", b"state")
    assert emulator.project("run-1")["checkpoint_digest"] == checkpoint["checkpoint_digest"]
