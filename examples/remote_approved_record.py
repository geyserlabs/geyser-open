"""A real Agent writes one synthetic record only after an exact human decision.

Use a disposable developer project with a qualified Open Agent. The record is
written in that task's workspace; this does not modify a ticketing service.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Literal

from geyser_sdk import ApprovalDecision, GeyserClient, InputCreate, TaskCreate, digest

ARGUMENTS = {
    "path": "reviewed-record.json",
    "content": '{"ticket_id":42,"status":"reviewed"}',
}


def submit(client: GeyserClient, operation_id: str) -> dict:
    if not client.capabilities().execution.get("write_approval_tasks"):
        raise RuntimeError("Select an Agent advertising write_approval_tasks.")
    value = client.upload_input(
        InputCreate(
            value={
                "instruction": (
                    "Create the synthetic reviewed record using exactly one Write call "
                    "with the supplied arguments. Wait for its human approval. If denied, "
                    "do not write or try another tool. Perform no other actions. "
                    "Return whether the write was approved or denied."
                ),
                "arguments": ARGUMENTS,
            }
        )
    )
    task = client.create_task(
        TaskCreate(
            input_ref=value.input.ref,
            input_digest=value.input.digest,
            require_write_approval=True,
            budget={
                "max_cost_usd": 1,
                "max_elapsed_seconds": 300,
                "max_provider_requests": 5,
                "max_tool_calls": 2,
            },
        ),
        idempotency_key=operation_id,
    ).task
    return {"task_id": task.id, "state": task.state, "run_id": task.run_id}


def decide(client: GeyserClient, approval_id: str, decision: Literal["approve", "reject"]) -> dict:
    approval = client.get_approval(approval_id).approval
    if approval.tool_name != "Write" or approval.arguments_digest != digest(ARGUMENTS):
        raise ValueError("This approval does not describe the exact example write.")
    intended = "approved" if decision == "approve" else "rejected"
    if approval.state == intended:
        # Recover a lost decision response by inspecting its committed state.
        return {"approval_id": approval_id, "state": intended, "recovered": True}
    if approval.state != "requested":
        raise ValueError("This approval already has a different terminal decision.")
    run = client.get_run(approval.run_id).run
    client.decide_approval(
        run.id,
        approval_id,
        ApprovalDecision(
            decision_id=f"example:{approval_id}:{decision}",
            decision=decision,
            expected_approval_sequence=approval.requested_sequence,
            binding_digest=approval.binding_digest,
            reason_code="reviewed_synthetic_record",
        ),
        expected_run_sequence=run.sequence,
    )
    return {"approval_id": approval_id, "state": intended}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("submit")
    create.add_argument("--operation-id", required=True)
    commands.add_parser("approvals")
    decision = commands.add_parser("decide")
    decision.add_argument("approval_id")
    decision.add_argument("decision", choices=["approve", "reject"])
    status = commands.add_parser("status")
    status.add_argument("task_id")
    args = parser.parse_args()
    credential = (
        "GEYSER_DEVELOPER_TOKEN"
        if args.command in {"approvals", "decide"}
        else "GEYSER_SERVICE_TOKEN"
    )
    with GeyserClient(os.environ["GEYSER_API_URL"], os.environ[credential]) as client:
        if args.command == "submit":
            value = submit(client, args.operation_id)
        elif args.command == "approvals":
            value = {"approvals": [item.model_dump() for item in client.list_approvals().data]}
        elif args.command == "decide":
            value = decide(client, args.approval_id, args.decision)
        else:
            task = client.get_task(args.task_id).task
            value = {"task_id": task.id, "run_id": task.run_id, "state": task.state}
            if task.state == "completed":
                value["result"] = client.result(task.id).result.value
    print(json.dumps(value, indent=2))


if __name__ == "__main__":
    main()
