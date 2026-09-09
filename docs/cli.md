# CLI reference

The **SDK/CLI 0.2.0** provides these commands. Global options (`--api-url`, `--profile`, `--json`, `--allow-file-credentials`) precede the command.

| Command | Behavior |
|---|---|
| `login [--scope SCOPE]` | Device login; stores the issued origin in the OS keychain |
| `login --service-token-stdin` | Save a bounded service token from stdin with its explicit issued API URL |
| `logout` | Remove the local profile; remote revocation is separate |
| `doctor` | Check the selected/stored API URL, schema version and local credential presence |
| `capabilities [--agent NAME]` | Read the project Agent’s execution readiness and runtime matrix; optional name must match |
| `init KIND NAME` | Create a scaffold |
| `validate PATH` | Validate package declarations and bounded file layout |
| `test PATH` | Execute frozen JSON handler cases in the OS sandbox |
| `dev PATH [--input FILE]` | Invoke a handler on supplied JSON or the first fixture |
| `package PATH` | Build deterministic ZIP bytes and print their digest |
| `sign ARCHIVE [--bundle FILE]` | Invoke the Sigstore CLI for exact archive bytes |
| `publish ARCHIVE --stage [--signature-bundle FILE]` | Upload a signed package; the default bundle is `ARCHIVE.sigstore.json` |
| `promote ID --digest DIGEST --canary` | Request installation on the project Agent |
| `promote ID --digest DIGEST --production` | Advance the same project’s stage and re-acknowledge installation |
| `status` | List package states; `pending_install` is not active |
| `revoke ID --digest DIGEST` | Revoke an exact package assignment |
| `tasks create --input FILE --idempotency-key KEY` | Upload JSON and submit a budgeted Agent task |
| `tasks list`, `tasks get ID`, `tasks result ID` | Inspect tasks and retrieve completed results |
| `tasks wait ID [--timeout SECONDS]` | Poll with a bounded deadline; timeout does not cancel remote work |
| `runs list`, `runs get ID`, `runs trace ID` | Inspect project run state and trace |
| `runs watch ID` | Emit each event immediately; `--json` emits newline-delimited JSON |
| `runs stop ID --expected-sequence N` | Request cancellation as a current owner/admin |
| `runs replay ID --mode MODE --expected-sequence N --idempotency-key KEY` | Create a project-owned new execution with enforced [replay limits](replay.md) |
| `runs fork ID --expected-sequence N [--mode MODE]` | Create a paused preview inspection record; it does not dispatch a replay |
| `approvals list`, `approvals get ID` | Read current approvals within the credential’s scope |
| `approvals decide RUN APPROVAL approve\|reject ...` | Submit a version- and digest-bound customer decision |
| `validate-outcome CONTRACT RESULT` | Check a JSON result against a local outcome contract |
| `version` | Print SDK/CLI source version |

Task creation accepts `--bundle PACKAGE_ID`, repeatable `--skill PACKAGE_ID`, `--model-profile PACKAGE_ID`, `--require-write-approval`, `--contract FILE`, `--package PACKAGE_ID`, `--max-cost`, `--max-seconds`, `--max-provider-requests`, and `--max-tool-calls`. Defaults are $1, 300 seconds, ten provider requests, and twenty tool calls. These are upper bounds, not included usage. A package task performs pure JSON execution and does not call a model.

Decision and package mutation commands show a preview. `--yes` skips that local prompt; server authorization and current-state checks still apply. `approvals decide` requires `--expected-approval-sequence` (or its `--expected-sequence` alias), `--expected-run-sequence`, `--binding-digest`, and `--reason-code`. Use the approval’s `requested_sequence` and the current run’s `sequence`, respectively. Run commands support `--customer` for authorized customer-wide inspection.

Human-readable mode is for a terminal; `--json` is for automation. Errors exit with code 2. Do not attach output containing private result values or credentials to public issues.
