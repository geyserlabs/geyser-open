# Runs, events, checkpoints, approvals, and effects

A run is admitted before provider use. Its append-only events use monotonic sequences and
idempotency identities. Checkpoints bind exact bytes by digest. Cancellation is a durable request,
not proof that a provider, tool, or specialist already stopped.

Consequential tool calls create an effect intent before execution and a receipt afterward. An
approval binds the run, tool, exact argument digest, consequence summary, risk class, data
boundary, and expiry. Argument drift or a stale sequence is denied. Unknown effects require
reconciliation rather than optimistic retry.

Trace export includes durable state, usage precision, budget enforcement, effects, approvals,
artifacts, evaluations, and event digests. It never exports hidden model reasoning.
