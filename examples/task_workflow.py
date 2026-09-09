"""Shared remote workflow. Use your issued Cell API URL and a service credential."""

from __future__ import annotations

import os
import time
from typing import Any

from geyser_sdk import GeyserClient, InputCreate, TaskCreate


def submit(
    value: Any,
    *,
    contract: dict[str, Any],
    operation_id: str,
    package_id: str = "",
    timeout: float = 300,
) -> dict[str, Any]:
    with GeyserClient(os.environ["GEYSER_API_URL"], os.environ["GEYSER_SERVICE_TOKEN"]) as client:
        capabilities = client.capabilities()
        mode = "extension" if package_id else "agent"
        if not capabilities.execution.get(mode + "_tasks"):
            raise RuntimeError("The assigned Agent does not advertise this execution mode.")
        uploaded = client.upload_input(InputCreate(value=value))
        outcome = client.upload_input(InputCreate(kind="outcome_contract", value=contract))
        task = client.create_task(
            TaskCreate(
                input_ref=uploaded.input.ref,
                input_digest=uploaded.input.digest,
                outcome_contract_ref=outcome.input.ref,
                budget={
                    "max_elapsed_seconds": timeout,
                    "max_cost_usd": 1.0,
                    "max_provider_requests": 10,
                    "max_tool_calls": 20,
                },
                metadata={"execution": mode, **({"package_id": package_id} if package_id else {})},
            ),
            idempotency_key=operation_id,
        ).task
        print("Task:", task.id, flush=True)
        deadline = time.monotonic() + timeout + 15
        while time.monotonic() < deadline:
            task = client.get_task(task.id).task
            if task.state == "completed":
                return {
                    "task_id": task.id,
                    "run_id": task.run_id,
                    "result": client.result(task.id).result.value,
                }
            if task.state in {"failed", "canceled"}:
                raise RuntimeError(f"Task {task.id} ended {task.state}; inspect run {task.run_id}.")
            time.sleep(5)
        raise TimeoutError(
            f"Task {task.id} remains {task.state}; keep its ID and inspect {task.run_id}."
        )
