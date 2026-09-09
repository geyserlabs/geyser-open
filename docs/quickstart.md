# Run your first handler

This is the **SDK/CLI 0.2.0**. It executes real Python code in an OS sandbox. You do not need an account, a model, or credentials.

## Install from source

Use Python 3.11–3.13 on macOS or Linux. Linux requires `bubblewrap` and permission to create user namespaces. macOS requires `sandbox-exec`. Execution fails closed if isolation is unavailable. Windows can use the HTTP SDK; this release has no Windows extension sandbox.

```console
git clone https://github.com/geyserlabs/geyser-open.git
cd geyser-open
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ./sdk/python -e ./cli
geyser --json version
```

The source version should be `0.2.0`. On Ubuntu, install `bubblewrap` using your administrator’s normal package-management process. Do not disable host security policy to bypass a failed sandbox check.

## Execute a tool

```console
geyser init tool word-count
geyser validate word-count
geyser test word-count
geyser --json dev word-count
```

`dev` returns `{"result":{"word_count":2},"sandboxed":true}`. `test` invokes the real handler with two frozen cases: successful word counting and rejection of an input that does not match its schema.

Edit `word-count/handler.py`, update `evals/cases.json` with expected outputs, and run the tests again. Validation checks declarations; it does not execute them. Tests and `dev` execute code.

```console
geyser package word-count
```

The package command prints the archive path and SHA-256 digest. This is a local archive, not an installed Agent capability. [Publisher trust and installation](extensions.md) are separate steps.

## Try a useful application

From the repository checkout:

```console
python examples/extension_app.py issue-normalizer
python examples/extension_app.py source-review-gate
```

The first normalizes an issue record. The second checks citation coverage. Both run their actual packaged handlers without network access. Read [recipes](recipes.md) to supply your own JSON or run the same package on an Agent.

The SDK’s [deterministic emulator](durable-runs.md) is also available for state-machine experiments. It is distinct from the OS sandbox and does not prove production behavior.
