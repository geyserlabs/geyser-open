# CLI reference

Local commands are `init`, `validate`, `validate-outcome`, `test`, `dev`, and `package`. Signing
is a separate `sign` step. Remote package lifecycle commands are `publish --stage`,
`promote --canary`, and `status`; the labels deliberately distinguish local bytes, registry
upload, staging, canary, and production promotion.

Operational commands are `runs list|get|watch|trace|fork|stop`,
`approvals list|get|decide`, and `capabilities`. `login`, `logout`, `doctor`, and `version`
manage the local client. Add global `--json` for stable machine output.

Mutating commands print an exact preview, send an idempotency identity, and require the applicable
credential. `--yes` confirms only that preview. The server remains the authority.
