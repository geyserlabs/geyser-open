# Geyser Open

Build applications around bounded Agent work, typed results, durable state and current customer authority. The repository contains the MIT-licensed sync/async Python SDK, CLI, OS-sandboxed JSON extension contract, deterministic emulator, actual server-exported OpenAPI, and executable reference applications.

**This source targets SDK/CLI 0.2.0.** Use the matching [published release](https://github.com/geyserlabs/geyser-open/releases/tag/v0.2.0) when available; an untagged checkout may include unreleased changes. Remote execution requires matching Cell and Agent software; a source merge is not a deployment.

```console
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ./sdk/python -e ./cli
geyser init tool word-count
geyser test word-count
geyser --json dev word-count
python examples/extension_app.py issue-normalizer
python examples/extension_app.py source-review-gate
```

Linux execution requires bubblewrap and allowed user namespaces; macOS requires sandbox-exec. Code is imported only after isolation. The HTTP SDK does not require a local sandbox. The in-memory emulator runs application-registered callbacks in your own process and is separate from extension isolation.

Start with [the quickstart](docs/quickstart.md), [reference applications](docs/recipes.md), [authentication](docs/authentication.md), and [costs, limits and support](docs/program.md). Apply [task-specific bundles](docs/bundles.md), require exact approvals before writes, or compare deliberate new executions with [replay modes](docs/replay.md). Read [availability and migration](docs/compatibility.md) before using a remote workspace.

Service credentials submit project work; human grants make authorized customer decisions; Agent keys produce run events. Credentials never silently change audience. Inputs/results and package bytes belong to the Customer Cell. The compatibility relay processes plaintext transiently; see [custody](docs/cells-privacy.md).

Use `make bootstrap` and `make check` to develop. Public schemas come from real server routes; do not hand-maintain an alternative OpenAPI. Report vulnerabilities privately under [SECURITY.md](SECURITY.md).
