# Run a new execution from an earlier input

The 0.2.0 source preview adds `client.replay` and `geyser runs replay` for a qualified Open Agent advertising the requested `replay_modes` entry. A replay creates a new project-owned task using the original task's immutable input. It has its own run, budget, results and approvals. It does not resume a saved model checkpoint or recover an uncertain external write.

| Mode | Actual execution boundary |
|---|---|
| `model_only` | Model execution with no tools |
| `tool_stubbed` | Only explicitly declared virtual tools; replies must match the tool name and canonical argument digest |
| `read_only_shadow` | `Read`, `Glob` and literal `Grep` within the new task workspace; its `input.json` contains the original input |
| `full_reexecution` | Current Agent tools, permissions and approval policy; requires a terminal parent, current customer owner and a new authority reference |

Read-only shadow does not read the original workspace or contact external systems. Stubbed mode never falls through to a live implementation. These two modes cannot activate ambient MCP tools, specialists or delegation. Missing stub replies fail the requested call.

```python
from geyser_sdk import ReplayCreate

parent = human_client.get_run(parent_run_id).run
child = human_client.replay(parent.id, ReplayCreate(
    fork_key="document-123:model-comparison:v1",
    expected_sequence=parent.sequence,
    mode="model_only",
    budget={"max_cost_usd": 1, "max_elapsed_seconds": 300,
            "max_provider_requests": 5, "max_tool_calls": 2},
)).task
```

`human_client` uses a current administrator/owner developer credential with `runs:manage` and `runs:read`. The SDK sends the parent version as `If-Match` and the stable `fork_key` as `Idempotency-Key`. Repeating the same request recovers the same child even if the parent subsequently advances. A changed principal, input binding, mode, target or budget under that key fails.

```sh
geyser runs replay "$PARENT_RUN_ID" --mode model_only \
  --expected-sequence "$PARENT_SEQUENCE" \
  --idempotency-key document-123:model-comparison:v1 --max-cost 1
```

The caller must inspect the current state after a stale-version response. Child creation and lineage are one atomic operation. `child.spec["_replay"]` and the resulting `run.execution["replay"]` identify the original task/run and explicitly state that historical approvals are not reused. Underscore-prefixed task fields are server-owned and cannot be supplied through task creation.

## Recorded tool replies

Upload an input object containing tool definitions and exact recorded replies, then supply its reference as `ReplayCreate(stubs_ref=...)` or `--stubs-ref`. It must belong to this project. For example:

```python
from geyser_sdk import InputCreate, digest

stubs = human_client.upload_input(InputCreate(value={
    "schema_version": 1,
    "tools": [{"name": "lookup_ticket", "description": "Return recorded ticket data",
               "parameters": {"type": "object", "properties": {"id": {"type": "integer"}},
                              "required": ["id"], "additionalProperties": False}}],
    "replies": [{"tool_name": "lookup_ticket", "args_digest": digest({"id": 42}),
                 "result": {"status": "open"}}],
})).input
```

Input upload also requires `tasks:write`. Schemas and arguments are validated with the same bounded JSON contract used for extensions. A stub set supports 32 tools and 128 replies, with a 256 KiB total bound. The Cell records the uploaded object's digest; later execution cannot substitute replies.

## Target and approval rules

The default target is the parent's model/profile/policy. Optional SDK target fields assert the current qualified selection; they do not install or switch models. If the Agent has changed, deliberately select its exact current model/profile/policy in a new request. Current package assignments are checked again, and revoked packages cannot execute.

Full re-execution requires `authority_ref` describing this new authorized operation. Its current permissions and fresh approvals still apply. The parent's `require_write_approval` restriction is preserved. `sanitized=True` is rejected: if input must change, upload the replacement and create a new task.

The older `fork` API remains a paused inspection record. Use it for inspection, `replay` for deliberate new execution, and the existing task identity for ordinary recovery. An unknown effect requires independently observed reconciliation before further consequential work.
