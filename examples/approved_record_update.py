"""Approve one exact synthetic record change and reconcile an interrupted response.

The control flow uses LocalEmulator; the SQLite write and operation receipt are
real. This is an application integration example, not a production Agent runtime.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Any

from geyser_sdk import LocalEmulator, TypedTask, digest
from geyser_sdk.emulator import EmulatorError


class TicketStore:
    def __init__(self, path: Path):
        self.path = path

    def initialize(self) -> None:
        # Create only a new, explicitly selected example database.
        self.path.touch(mode=0o600, exist_ok=False)
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE tickets(id INTEGER PRIMARY KEY, status TEXT, version INTEGER)")
            db.execute("CREATE TABLE operations(id TEXT PRIMARY KEY, request TEXT, result TEXT)")
            db.execute("INSERT INTO tickets VALUES(42, 'open', 1)")

    def read(self) -> dict[str, Any]:
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT status,version FROM tickets WHERE id=42").fetchone()
        return {"ticket_id": 42, "status": row[0], "version": row[1]}

    def result(self, operation_id: str, arguments: dict[str, Any]) -> dict[str, Any] | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute(
                "SELECT request,result FROM operations WHERE id=?", (operation_id,)
            ).fetchone()
        if row is None:
            return None
        if row[0] != digest(arguments):
            raise ValueError("operation_id belongs to another exact change")
        return json.loads(row[1])

    def update(self, operation_id: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if (
            set(arguments) != {"ticket_id", "expected_version", "status"}
            or type(arguments["ticket_id"]) is not int
            or arguments["ticket_id"] != 42
            or type(arguments["expected_version"]) is not int
            or arguments["expected_version"] < 1
            or arguments["status"] not in {"open", "reviewed"}
        ):
            raise ValueError("invalid synthetic ticket change")
        with sqlite3.connect(self.path) as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute(
                "SELECT request,result FROM operations WHERE id=?", (operation_id,)
            ).fetchone()
            if old:
                if old[0] != digest(arguments):
                    raise ValueError("operation_id belongs to another exact change")
                return json.loads(old[1])
            changed = db.execute(
                "UPDATE tickets SET status=?,version=version+1 WHERE id=? AND version=?",
                (arguments["status"], arguments["ticket_id"], arguments["expected_version"]),
            )
            if changed.rowcount != 1:
                raise ValueError("record changed since the proposal was inspected")
            result = {
                "ticket_id": 42,
                "status": arguments["status"],
                "version": arguments["expected_version"] + 1,
            }
            db.execute(
                "INSERT INTO operations VALUES(?,?,?)",
                (operation_id, digest(arguments), json.dumps(result)),
            )
        return result


async def demonstrate(store: TicketStore, *, approve: bool, lose_response: bool) -> dict[str, Any]:
    emulator = LocalEmulator()
    run_id, operation_id, approval_id = "run_ticket_42", "ticket-42:review:v1", "approval_ticket_42"
    arguments = {"ticket_id": 42, "expected_version": 1, "status": "reviewed"}
    emulator.admit(
        run_id,
        TypedTask(
            task_id="task_ticket_42", context_id="ticket_42", prompt_digest=digest(arguments)
        ),
    )
    calls = 0

    def change(value: dict[str, Any]) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        result = store.update(operation_id, value)
        if lose_response:
            raise ConnectionError("Synthetic response interruption after the database commit")
        return result

    emulator.register_tool("update_ticket", change)
    binding = {
        "run_id": run_id,
        "tool_name": "update_ticket",
        "arguments_digest": digest(arguments),
        "operation_id": operation_id,
    }
    approval = emulator.request_approval(run_id, approval_id=approval_id, binding=binding)
    emulator.decide_approval(
        approval_id, binding_digest=approval["binding_digest"], approve=approve
    )

    async def invoke() -> Any:
        return await emulator.call_tool(
            run_id,
            tool_name="update_ticket",
            arguments=arguments,
            approval_id=approval_id,
            operation_id=operation_id,
        )

    if not approve:
        try:
            await invoke()
        except EmulatorError:
            return {"decision": "rejected", "tool_invocations": calls, "record": store.read()}
        raise AssertionError("a rejected operation must not execute")
    try:
        result = await invoke()
    except ConnectionError:
        # The application queries its actual system of record before settling
        # uncertainty. It does not infer success from the proposed arguments.
        try:
            await invoke()
        except EmulatorError:
            pass
        else:
            raise AssertionError("an uncertain write must require reconciliation")
        result = store.result(operation_id, arguments)
        if result is None:
            raise RuntimeError(
                "the write remains unresolved; ask an operator to inspect it"
            ) from None
        effect = emulator.events[run_id][-1]["data"]["effect_id"]
        emulator.reconcile_tool(run_id, effect_id=effect, result=result)
    assert await invoke() == result
    return {
        "decision": "approved",
        "reconciled": lose_response,
        "tool_invocations": calls,
        "record": store.read(),
    }


def main() -> None:
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="geyser-approved-record-") as directory:
        outcomes = []
        for index, (approve, interrupted) in enumerate(
            ((False, False), (True, False), (True, True))
        ):
            store = TicketStore(Path(directory) / f"example-{index}.sqlite")
            store.initialize()
            outcomes.append(
                asyncio.run(demonstrate(store, approve=approve, lose_response=interrupted))
            )
    print(
        json.dumps(
            {
                "mode": "local application example",
                "outcomes": outcomes,
                "model_requests": 0,
                "model_cost_usd": 0,
                "elapsed_seconds": round(time.perf_counter() - started, 4),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
