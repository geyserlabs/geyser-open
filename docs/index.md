# Build applications around work you can inspect

Geyser is useful when your application needs an Agent to do bounded work, return a typed result, and leave a durable record of decisions and effects. Start with one workflow: normalize incoming issues, review supplied material, or evaluate an output before your application accepts it.

**This documentation describes the 0.2.0 source preview.** Published SDK/CLI 0.1.0 does not contain these execution and security corrections. Remote execution requires a matching Customer Cell and Agent rollout; installing a new SDK cannot upgrade a workspace. Check [availability](compatibility.md) before connecting.

## Choose a useful first project

| Build | What you get | Start here |
|---|---|---|
| Issue intake | Validated issue JSON normalized into a stable application record | [Reference applications](recipes.md) |
| Output review gate | A deterministic check that every claim cites a supplied source ID | [Reference applications](recipes.md) |
| Agent document review | A budgeted Open Agent task with a JSON result and inspectable run | [Python SDK](sdk.md) |
| An existing integration | Idempotent task submission, event cursors, scoped access and result retrieval | [Authentication](authentication.md) |

The review gate checks reference coverage. It does not establish that a claim is factually true. Keep the human or domain-specific review your application needs.

## Why use Geyser?

Use Geyser when you need durable task identity, current workspace authority, inspectable effects and approvals, and customer-controlled data custody together. A direct model API may be enough for a one-shot text transformation. A normal function is simpler for isolated deterministic business logic; packaging that function is useful when you want the same validated bytes tested locally and installed on a customer Agent.

The public SDK and CLI are MIT-licensed. Models, Agent compute, and external tools come from your workspace and may incur charges. See [costs, limits and support](program.md).

## First success

Run an actual credential-free handler in the [quickstart](quickstart.md), then create a project in the console’s **Developers** page. Submit a small task, read its result, and inspect its run before adding your application’s own behavior.

No external adoption, independent certification, or bug-free guarantee is claimed. The repository includes executable examples and regression tests; [try the workflow](external-preview.md) and report where it fails for your use case.
