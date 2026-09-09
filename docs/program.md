# Costs, limits, support and feedback

## Costs

The open SDK, CLI and examples have an MIT license. Local pure handlers require no model and make no network calls. Remote work uses your workspace’s Agent compute, models and authorized services, which may be billable under your existing account configuration. No free compute allowance, special developer credit, or fixed per-task price is promised here.

Set task ceilings for elapsed seconds, provider requests, tool calls and cost. Admission preserves the submitted ceilings and required capabilities. Runtime budget enforcement follows the qualified adapter and provider accounting; cost estimates and in-flight requests are not a guarantee of a provider’s final invoice. Compare measured task quality, latency and actual account usage against your baseline before increasing traffic.

## Operational limits

| Item | Current bound |
|---|---|
| Public project credential | 60 requests per minute; `429` includes `Retry-After` |
| Recommended polling | At least five seconds between polls |
| JSON input/result | 1 MiB per object |
| Handler invocation | At most 30 seconds; default 512 MiB configured memory bound |
| Package | 10 MiB unpacked, 2 MiB per file, 512 entries |
| Installation tests | 1–32 cases; two seconds each and ten seconds total |
| Desired package assignments | 200 per Agent |
| Developer worker | One task at a time per Agent; shares the Agent’s compute |
| Task ownership | Expiring lease, renewed while running; stale owners cannot publish |
| CLI-created service credential | Explicit issued API URL; console expiry choices 1, 7 or 30 days |
| API credential lifetime | Human grants at most 30 days; service credentials at most 366 days; default OAuth token one day |

An Agent can be unavailable or occupied. Queue time is not a latency SLA. Human approval and effect reconciliation can delay completion. Cancellation is acknowledged only after the execution adapter stops; already committed external effects are not undone.

Retention uses your customer run-retention policy (30 days by default). Active task inputs are retained; old terminal tasks and unreferenced objects are removed. Revoked projects age out under that policy. Agent deletion erases owned developer objects and package records. Your application must delete its own retained copies separately.

## Support and security

Report reproducible bugs in [GitHub Issues](https://github.com/geyserlabs/geyser-open/issues). Include the SDK/CLI version, OS, API version, safe error code, expected behavior and a minimal synthetic example. Never include a token or private content. The preview has no general support-response or availability SLA. Security reporting follows the [security policy](security.md).

## What we want to learn

Before expanding the program, test with developers outside Geyser using only the public guides. Measure time to the first local handler, first completed remote task, recovery from a lost connection, and a useful repeated workflow. Initial product targets are a first local result within ten minutes and a first remote result within thirty minutes after workspace access; these are experiment targets, not measured outcomes or guarantees.

Ask whether the developer would keep using the integration after the exercise, what simpler alternative they would choose, and whether durable state, authority and custody saved meaningful implementation work. Track returning use and actual task quality, not just sign-ups or package downloads. No external adoption results are asserted by these examples.

The console’s Developers page shows this project’s last seven days of retained task counts and mean time from submission to completion, including queueing. No external analytics service receives task content. Use these operational counts alongside interviews and observed first-use sessions; they do not establish adoption or customer value.
