# Python SDK

The examples below target the **SDK/CLI 0.2.0** and an upgraded, ready workspace. Use your issued Cell API URL, not a guessed global API host.

## Submit a bounded task and retrieve its result

```python
import os
from geyser_sdk import GeyserClient, InputCreate, TaskCreate

with GeyserClient(os.environ["GEYSER_API_URL"], os.environ["GEYSER_SERVICE_TOKEN"]) as client:
    capabilities = client.capabilities()
    if not capabilities.execution.get("agent_tasks"):
        raise RuntimeError("Select a ready, qualified Open Agent")

    uploaded = client.upload_input(
        InputCreate(
            value={
                "instruction": "Summarize the supplied text. Do not perform external actions.",
                "text": "A short, application-provided document.",
            }
        )
    )
    contract = client.upload_input(
        InputCreate(
            kind="outcome_contract",
            value={
                "schema_version": 1,
                "schema_ref": "example:summary:1",
                "json_schema": {
                    "type": "object",
                    "properties": {"summary": {"type": "string", "maxLength": 2000}},
                    "required": ["summary"],
                    "additionalProperties": False,
                },
            },
        )
    )
    submitted = client.create_task(
        TaskCreate(
            input_ref=uploaded.input.ref,
            input_digest=uploaded.input.digest,
            outcome_contract_ref=contract.input.ref,
            budget={
                "max_cost_usd": 1.0,
                "max_elapsed_seconds": 300,
                "max_provider_requests": 10,
                "max_tool_calls": 20,
            },
            metadata={"execution": "agent"},
        ),
        idempotency_key="document-123:summary:v1",
    )
    print(submitted.task.id)
```

Use a stable business operation ID and keep it if the response is interrupted. Reuse with identical input returns the existing task; reuse with different input or requirements returns `409 idempotency_key_reused`.

Poll `client.get_task(task_id)` no faster than every five seconds. Once `task.state == "completed"`, call `client.result(task_id)`; `result.value` is the customer-owned JSON. Without an outcome contract, Open Agent results have the shape `{"text": "..."}`. A task may instead fail, be canceled, or remain claimed while its run needs an approval or effect reconciliation. Inspect `task.run_id` when present.

Inputs must be uploaded project-owned references. Arbitrary URLs, local paths, and opaque references from another project are rejected. The result is committed before terminal completion; no raw input/result is written into the Agent’s control spool. See [custody](cells-privacy.md).

## Run the same JSON extension remotely

Set `metadata={"execution": "extension", "package_id": "YOUR_ACTIVE_PACKAGE_ID"}` on the task. The package must be active in this project after the assigned Agent verifies its signature and passes its real sandboxed cases. Pure extensions do not receive model, network, subprocess, or credential access.

`examples/task_workflow.py` contains submission, capability checks, bounded polling, terminal-state handling and result retrieval. `examples/agent_review.py` and `examples/extension_app.py` are complete applications built on that workflow.

## Inspect runs and events

```python
for event in client.watch_events(run_id, after_sequence=last_sequence):
    save_cursor(event.sequence)
    handle_event(event)
```

Here `client`, `run_id`, `save_cursor` and `handle_event` belong to your application. The iterator emits events as they arrive and drains events observed at completion before returning. Save sequence cursors for reconnects. For customer-wide inspection, pass `customer=True` with an authorized customer/developer grant; project grants remain restricted to their project and current Agent assignment.

`trace(run_id)` returns content-free timing, usage and effect information. `list_tasks`, `list_runs`, `list_packages` and approval pages return cursors. Follow `next_cursor`, including on an empty filtered page.

## Decisions and errors

Cancellation uses `CancelRequest(cancellation_id="can_...", expected_sequence=sequence, reason_code="...")`. Evaluation and fork requests also carry `expected_sequence`; it must agree with `If-Match`. A stale decision returns `412`. Inspect the current state before deciding again. Approvals additionally bind the exact approval and argument digest. Read `approval.requested_sequence` for `ApprovalDecision.expected_approval_sequence`; pass the current run sequence separately to `decide_approval(..., expected_run_sequence=run.sequence)`.

Forks are **preview inspection records**. They create a paused child record from a checkpoint; the separate [replay API](replay.md) dispatches a deliberately new task. Do not use them as a job retry mechanism.

The SDK raises `ProblemError` for RFC problem details, `ResponseValidationError` for an incompatible response and `TransportError` when no response is available. Retries are bounded and honor `Retry-After`; long retry delays are returned to your application instead of sleeping indefinitely. Idempotent creation can be retried; unknown consequential effects require reconciliation, not blind resubmission.

## Async applications

`AsyncGeyserClient` exposes the same operations with `await`, async context management and async iterators. Reuse a client and close it. Do not store credentials in source code; a token-provider callback can read your own secret manager.

## Task-specific instructions

Use `bundle_package_id`, `skill_package_ids`, and `model_profile_package_id` on `TaskCreate` to select active signed packages. Use `require_write_approval=True` to require exact human decisions before consequential calls. These options need the corresponding advertised execution flags. See [bundles](bundles.md) for formats, applied-content reports and omitted references.
