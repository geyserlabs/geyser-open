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

## Authority model

Developer/service credentials can create project tasks and inspect project
runs. Customer credentials can make customer decisions. Agent credentials can
produce runtime events. The SDK never exchanges or silently upgrades one
credential class into another.

## Status

This repository is public, but its initial packages are not yet a published
release. Installation URLs and checksums become authoritative only after the
signed Developer Preview release gate.
Public Geyser SDK, CLI, emulator, schemas, conformance, and developer documentation
