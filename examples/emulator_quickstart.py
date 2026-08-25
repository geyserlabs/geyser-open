"""Credential-free durable run, approval, tool, checkpoint, and completion."""

from __future__ import annotations

import asyncio
import json

from geyser_sdk import LocalEmulator, TypedTask, digest


async def main() -> None:
    emulator = LocalEmulator()
    task = TypedTask(
        task_id="task_example",
        context_id="context_example",
        prompt_digest=digest("store the approved value"),
        model_ref="deterministic:answer",
    )
    emulator.admit("run_example", task)
    emulator.register_tool("store", lambda arguments: {"stored": arguments["value"]})
    arguments = {"value": 42}
    binding = {
        "run_id": "run_example",
        "tool_name": "store",
        "arguments_digest": digest(arguments),
    }
    approval = emulator.request_approval(
        "run_example", approval_id="approval_example", binding=binding
    )
    emulator.decide_approval(
        "approval_example", binding_digest=approval["binding_digest"], approve=True
    )
    await emulator.call_tool(
        "run_example", tool_name="store", arguments=arguments, approval_id="approval_example"
    )
    emulator.checkpoint("run_example", b'{"next":"complete"}')
    emulator.append(
        "run_example",
        event_type="run.completed",
        key="completion",
        expected_sequence=emulator.project("run_example")["sequence"],
    )
    print(json.dumps(emulator.project("run_example"), indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
