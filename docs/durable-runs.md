# Durable tasks, runs and effects

A developer task begins `queued`, becomes `claimed` by its assigned Agent, and ends `completed`, `failed`, or `canceled`. The Agent claims a stable run ID with a versioned, expiring ownership lease. Recovery preserves that run ID and increments a fencing token; an older process cannot renew, read task input, produce run events or publish a result after ownership changes.

The task’s input digest, required capabilities, budget ceilings, project and outcome-contract reference must match admission. Unsupported modes are rejected before queueing. Inputs/results belong to the Customer Cell; event metadata contains references and digests.

The worker commits the result before completion. If acknowledgement is lost, recovery checks for a committed result and completes the existing run without invoking the handler or provider again. Terminal run state is projected back onto the task.

A run may pause for approval, billing, or recovery while its task remains claimed. An external effect whose outcome is unknown is not retried automatically. Reconcile the actual outcome through the workspace’s authorized controls before continuing. Idempotent submission cannot make an arbitrary third-party side effect exactly-once.

Cancellation records a request and an adapter acknowledgement before the canceled state. It stops future work; it does not undo a committed effect. Events use increasing sequence numbers. `watch_events` drains the terminal sequence, and saved cursors support reconnects.

## Local emulator

`LocalEmulator` simulates durable control state with application-registered model and tool callbacks. It is in-memory test machinery, not a production runtime or sandbox. Its callbacks execute in your process and have that process’s authority. Use synthetic data and deterministic fakes.

After an injected crash following `tool.started`, the emulator refuses to invoke that effect again. Record an independently observed result with `reconcile_tool` before continuing. Completed/reconciled calls return the recorded result. Use a fresh operation identity for a deliberately distinct effect.

## Forks

The public fork operation creates a paused inspection record tied to a checkpoint. It does not dispatch a new execution, reuse historical approvals, or provide an automatic replay engine. Treat it as preview functionality; use a new, explicitly authorized task for new work.
