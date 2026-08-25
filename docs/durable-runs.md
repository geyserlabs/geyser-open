# Runs, events, checkpoints, approvals, and effects

A run is admitted before provider use. Its append-only events use monotonic sequences and
idempotency identities. Checkpoints bind exact bytes by digest. Cancellation is a durable request,
not proof that a provider, tool, or specialist already stopped.

## Approvals, effects, and idempotency

Consequential tool calls create an effect intent before execution and a receipt afterward. An
approval binds the run, tool, exact argument digest, consequence summary, risk class, data
boundary, and expiry. Argument drift or a stale sequence is denied. Unknown effects require
reconciliation rather than optimistic retry.

Every retryable mutation carries a stable idempotency key. Reusing that identity with different
arguments is a conflict, not a second action. A crash after the external effect but before its
receipt leaves the effect `unknown` until an adapter-specific reconciliation proves what happened.

## Trace, replay, and fork

Trace export includes durable state, usage precision, budget enforcement, effects, approvals,
artifacts, evaluations, and event digests. It never exports hidden model reasoning.

Replay re-evaluates retained evidence without repeating consequential effects. Fork creates a new
run from an eligible checkpoint with a new identity and explicit authority evaluation. Neither
operation rewrites the original event stream.
