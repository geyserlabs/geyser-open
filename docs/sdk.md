# Python SDK

Use `GeyserClient` in a synchronous application and `AsyncGeyserClient` in an asynchronous one.
Both expose typed operations for tasks, runs, events, approvals, effects, artifacts, and packages.

## Read your runs

Supply a scoped developer token through your application's secret source. This example reads it
from `GEYSER_TOKEN` and prints only run IDs and states:

```python
import os
from geyser_sdk import GeyserClient

with GeyserClient(
    "https://agents.geyserlabs.ai",
    os.environ["GEYSER_TOKEN"],
    timeout=30.0,
) as client:
    for run in client.iter_runs():
        print(run.id, run.state)
```

`iter_runs` follows pagination for you. Use `list_runs` if you want to manage page cursors yourself.
[Authentication](authentication.md) explains how credentials are scoped to your project.

## Follow a run through reconnects

Keep the last event sequence your application has processed. Pass it back when you reconnect:

```python
import os
from geyser_sdk import GeyserClient

run_id = os.environ["GEYSER_RUN_ID"]
last_sequence = int(os.environ.get("GEYSER_AFTER_SEQUENCE", "0"))

with GeyserClient(
    "https://agents.geyserlabs.ai",
    os.environ["GEYSER_TOKEN"],
    timeout=30.0,
) as client:
    for event in client.watch_events(run_id, after_sequence=last_sequence):
        print(event.sequence)
        # Persist this sequence after your application processes the event.
        last_sequence = event.sequence
```

`watch_events` follows committed events and finishes when the run is terminal and its events have
been read. Persist your cursor alongside the work your application does with each event. See
[durable execution](durable-runs.md) for retries, checkpoints, and effects.

## Use the async client

```python
import asyncio
import os
from geyser_sdk import AsyncGeyserClient

async def main():
    async with AsyncGeyserClient(
        "https://agents.geyserlabs.ai",
        os.environ["GEYSER_TOKEN"],
        timeout=30.0,
    ) as client:
        async for run in client.iter_runs():
            print(run.id, run.state)

asyncio.run(main())
```

## Choose the operation

| Your application needs to… | SDK entry point |
|---|---|
| Submit authorized work | `create_task(task, idempotency_key=...)` |
| Read a task and its state | `get_task(task_id)` |
| List runs | `list_runs(...)` or `iter_runs(...)` |
| Read a run | `get_run(run_id)` |
| Fetch an event page | `events(run_id, after_sequence=...)` |
| Follow progress | `watch_events(run_id, after_sequence=...)` |
| Check an Agent's capabilities | `capabilities(agent_name=...)` |

Use the [API and schema reference](reference.md) for request fields and response shapes.

## Connection and error behavior

Clients reuse their HTTP connection and close it when the context manager exits. The default timeout
is 30 seconds; set `timeout` to match your application. Tokens can be strings or callables that
retrieve the current credential.

Reads and mutations with an idempotency key can retry. Conditional decisions send `If-Match`.
A stale sequence or approval binding produces a typed `ProblemError`; read the latest state before
making a new decision. See [troubleshooting](troubleshooting.md).

API v1 may add response fields. Output models preserve those fields, while input models reject
unknown fields so a typo cannot silently change the meaning of a request.
