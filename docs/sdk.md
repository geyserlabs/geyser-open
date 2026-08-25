# Python SDK

`GeyserClient` and `AsyncGeyserClient` provide typed task, run, event, approval, effect, trace,
evaluation, fork, artifact, package, and capability operations. Both reuse their HTTP connection,
require an explicit timeout, and accept either an explicit token or a callable token provider.

Only reads and mutations carrying an idempotency key are retried. Conditional decisions send
`If-Match`; stale sequences and approval bindings become typed `ProblemError` values. List
operations provide pages and iterators. `watch_events` resumes after the last durable sequence,
so a reconnect does not invent or skip committed events.

```python
from geyser_sdk import GeyserClient

with GeyserClient("https://agents.geyserlabs.ai", token) as client:
    for run in client.iter_runs():
        print(run.id, run.state, run.runtime_profile_digest)
```

The server may add fields within API v1. Output models preserve additive fields, while input
models reject unknown fields to prevent accidental authority or behavior changes.
