# Recipes and examples

- Use the emulator to inject a crash immediately after `tool.started`; restart from the durable
  event and reconcile the effect before deciding whether execution is safe.
- Use `validate-outcome` in CI to freeze an exact Draft 2020-12 result schema. External `$ref`
  values are rejected so validation never fetches ambient network content.
- Compare `runtime_profile_digest`, `model_profile_digest`, and
  `qualification_evidence_digest` before selecting a runtime. A framework label is not enough.
- Use `runs watch` to reconnect after the latest observed event sequence and `runs trace` for an
  auditable export without hidden reasoning.

See `examples/emulator_quickstart.py`, `examples/sync_client.py`, and
`examples/async_client.py`. All public examples use fake IDs or local-only execution.
