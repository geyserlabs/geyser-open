# Availability and compatibility

## Release status

**0.2.0 is the source preview described by these docs.** The published Python, standalone and Homebrew release remains 0.1.0 until a separate release is published. A source merge, a published package and a running Cell/Agent are distinct states. Do not assume the new execution path exists on a workspace running older software.

| Surface | 0.2.0 source behavior | Prerequisite |
|---|---|---|
| Sync/async SDK | Owned input upload, tasks, results, events, traces, decisions and package lifecycle | Python 3.11–3.13; matching public API |
| Local JSON extensions | Real handler tests and execution | macOS sandbox-exec, or Linux bubblewrap with permitted user namespaces |
| Remote Agent tasks | Qualified Open runtime only | Cell and Agent advertise protocol 1 and `agent_tasks: true` |
| Remote JSON extensions | Signed, tested pure handlers | Agent advertises `extension_tasks: true`; exact package is active |
| Skills/model profiles/Agent Bundles | Verified per-task instructions and context; exact current model/policy assertions | `bundle_tasks: true`; active project packages |
| Approval-required tasks | Every consequential call waits for an exact human decision | `write_approval_tasks: true`; current owner/admin |
| Replays | Four enforced execution modes create a new task | Advertised mode; current administrator/owner and target binding |
| Forks | Paused inspection records | No public replay dispatch |
| Third-party OAuth applications | Not offered | Current OAuth client is the Geyser CLI |
| Windows extension execution | Not offered | HTTP SDK remains usable |

`geyser capabilities` reports the assigned Agent’s `execution` flags and runtime matrix. The server rejects tasks whose execution mode is unavailable. A missing qualified model profile can coexist with usable pure JSON extensions.

Capabilities report `native`, `geyser_emulated`, `unsupported`, or `forbidden`. `review_due` means the qualification evidence reached its review date; current server policy determines whether a last-known-good profile remains usable. A local emulator result never grants a production capability.

## Migrating from 0.1.0

0.2.0 corrects broken contracts and narrows unsafe behavior. Reauthenticate old CLI profiles so credentials acquire an exact API URL. Upload inputs before task creation. Evaluation/fork requests carry the current sequence; fork responses contain `parent_run` and `child_run`. Approval decisions use the approval’s `requested_sequence` in the body and the current run sequence as `expected_run_sequence` in the SDK (the CLI requires both). Cancellation IDs use `can_...`. Watch output streams immediately instead of returning a buffered array. Frozen extension cases must execute code and assert results. Configure a trusted publisher and re-verify old packages; old “active” metadata alone is insufficient.

Pin versions and inspect the current [OpenAPI](reference.md). We do not claim an untested rolling compatibility window across these corrections. Security fixes can immediately remove unsafe access. Published artifacts remain immutable and receive a new version when changed.
