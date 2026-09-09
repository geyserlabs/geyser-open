# Changelog

## 0.2.0 — source preview, not yet published

- Current membership, Agent assignment, session audience, project and Cell generation are rechecked for developer access.
- CLI profiles bind credentials to the issued API URL. Exact loopback checks reject deceptive HTTP hosts.
- Publisher trust is administrator-owned; Cell and Agent verify exact Sigstore archive bytes and identity. Installation becomes active only after real sandboxed tests and a current acknowledgement.
- Owned JSON inputs, typed results and an Agent task consumer replace metadata-only task acceptance. Admission preserves capabilities, budgets and outcome contracts; expiring claims fence stale workers.
- Sync/async evaluation, cancellation and fork contracts match the server. Event watching streams immediately and drains terminal events; retry delays honor server rate limits.
- Unknown emulator effects require reconciliation. Scaffolds execute real JSON handlers. New issue-normalization, source-review and Agent-review applications show useful workflows.
- Console project/credential/publisher setup and explicit revocation are available with the matching server rollout. OpenAPI is exported from actual server routes.
- Agent HTTP runtime dependencies move to corrected httpx2/httpcore2 releases. Configuration-only extension types and undispatched forks are labeled as previews.

Read [migration details](compatibility.md). Publishing SDK artifacts and rolling out Cell/Agent software are separate release actions; source availability does not assert either has occurred.

## 0.1.0 — published

Initial public Python SDK/CLI, standalone CLI, Homebrew distribution, emulator, schema and documentation release. It does not include the 0.2.0 corrections above. Existing release bytes remain immutable.
