# Geyser Open — Developer Preview

Geyser Open is the public, framework-neutral developer surface for building and
operating durable agentic work on Geyser. This monorepo contains:

- `geyser-sdk`: a typed sync/async Python client and deterministic local emulator;
- `geyser-open`: the `geyser` developer CLI;
- versioned schemas and the public OpenAPI contract;
- extension scaffolds, conformance fixtures, examples, and documentation.

The SDK and CLI do **not** include an Agent runtime, provider SDK, brain, model,
browser, VM, or ambient credentials. Installing them does not grant authority.
Server-side customer/project scopes, policy composition, task requirements,
approval bindings, and runtime qualification remain authoritative.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e './sdk/python[test]' -e './cli[test]'
geyser init tool careful-search
geyser validate careful-search
geyser test careful-search
```

Then try the deterministic emulator:

```bash
python examples/emulator_quickstart.py
```

Developer Preview currently targets Python 3.11–3.13, macOS Apple Silicon, and
Ubuntu 24.04 AMD64. See [docs/compatibility.md](docs/compatibility.md),
[SECURITY.md](SECURITY.md), and [CONTRIBUTING.md](CONTRIBUTING.md).
Release verification, SBOM, provenance, and revocation guidance is in
[docs/releases.md](docs/releases.md).

## Authority model

Developer/service credentials can create project tasks and inspect project
runs. Customer credentials can make customer decisions. Agent credentials can
produce runtime events. The SDK never exchanges or silently upgrades one
credential class into another.

## Status

Developer Preview `0.1.0b4` is published on
[PyPI](https://pypi.org/project/geyser-sdk/0.1.0b4/) and
[GitHub Releases](https://github.com/geyserlabs/geyser-open/releases/tag/v0.1.0b4)
from source commit `b105031a2de27633a183d82729b375168b138fcf`. Clean public-index
installs and the signed standalone artifacts are qualified on Apple-Silicon
macOS and native AMD64 Ubuntu. Homebrew publication and production enablement
remain separate status gates; see the [compatibility matrix](docs/compatibility.md).
Public Geyser SDK, CLI, emulator, schemas, conformance, and developer documentation
