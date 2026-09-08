# Build something your team can use

Geyser brings people and AI agents together with computers, connected apps, and shared projects.
The developer tools let you extend what those agents can do and build applications around their work.

Start locally. Create a tool, test its behavior, and follow a run from request to result. When you're
ready, connect to your Geyser workspace with the same SDK and CLI.

## Choose your first step

| What you want to do | Start here |
|---|---|
| Try Geyser's development workflow without an account | [Five-minute quickstart](quickstart.md) |
| Give an Agent a new tool or connection | [Build an extension](extensions.md) |
| Read runs and follow progress from your application | [Python SDK](sdk.md) |
| Sign in and work with your own workspace | [Authentication](authentication.md) |
| Validate a result or recover after an interruption | [Practical recipes](recipes.md) |

## What is open

The Python SDK, CLI, local emulator, schemas, and examples are MIT-licensed in
[Geyser Open](https://github.com/geyserlabs/geyser-open). Use them with your existing application
or agent framework. The SDK connects to Geyser's API; your workspace supplies the Agent runtime,
models, tools, and access.

## What you can build on

A **task** describes the work. A **run** tracks its execution. Ordered **events** let your application
follow progress and reconnect after an interruption. **Checkpoints** preserve a known point in the
work. **Approvals** bind a person's decision to a specific action, and **effects** record what that
action did.

Read [how durable execution works](durable-runs.md), or go straight to a
[working local example](quickstart.md#follow-a-complete-run).

## Current release

SDK and CLI **0.1.0** support Python **3.11–3.13**. Standalone CLI builds are available for Apple
silicon macOS and Ubuntu 24.04 AMD64. See [compatibility](compatibility.md) for API versions and
[releases](releases.md) for install and verification links.

Looking for the product instead? Visit [Geyser](https://www.geyserlabs.ai),
[open your workspace](https://agents.geyserlabs.ai), or follow the
[customer guides](https://www.geyserlabs.ai/guides).
