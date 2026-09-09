# Troubleshooting

| Symptom | What to check |
|---|---|
| Local handler cannot run | `bubblewrap`/user namespaces on Linux, `sandbox-exec` on macOS; no unsandboxed fallback exists |
| Tests pass but no remote capability | Local tests do not install packages; check exact publisher trust and `pending_install`/`active` state |
| Task rejected before queueing | Assigned Agent must advertise the selected protocol-1 execution mode |
| `401 invalid_project_credential` | Expiry, revocation, old profile, Cell generation, and the exact issued API URL |
| `403 project_scope_denied` | Request only the needed scope and obtain fresh consent; service tokens cannot make human decisions |
| `409 idempotency_key_reused` | Use the original request bytes or choose a new key for genuinely new work |
| `412` after a decision | Inspect the current version and binding; do not silently overwrite another decision |
| Claimed task appears stuck | Inspect its run for pending approval, billing pause or unknown effects; do not resubmit an uncertain effect |
| Completed task has no result | Verify matching 0.2.0 Cell/Agent software; old producers did not commit developer results |
| `429` | Honor `Retry-After`, reuse a client and poll at least five seconds apart |
| `install_failed` | Verify sandbox readiness, exact signature/publisher and bounded frozen cases; corrected bytes need a new package version |
| Fork remains paused | Public forks are inspection records; replay dispatch is not available |

Use `geyser doctor`, `geyser capabilities`, `geyser tasks get ID`, `geyser runs get ID`, and `geyser status` to inspect the relevant layer. Include only synthetic data and safe error codes in support reports.
