# Emulator

`geyser_sdk.LocalEmulator` is in-process, deterministic, single-tenant, and has no network or
credential loader. It models durable event order, idempotency, crash-after-commit, checkpoints,
structured outcomes, deterministic model/tool registration, and exact approval binding. It is a
development and conformance tool, not a production Agent runtime.
