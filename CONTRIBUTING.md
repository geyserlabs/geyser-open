# Contributing

Open an issue before a large change. Use a focused branch, add frozen success and denial cases,
and run `make check`. Contributions must not add runtime, model-provider, brain, browser, VM, or
ambient-credential dependencies to `geyser-sdk`.

Generated schemas are checked in. Change the semantic model first, run
`uv run python scripts/generate_schemas.py`, and review the generated diff. Security-sensitive
changes require a threat-model update and two-person review. By participating you agree to the
[Code of Conduct](CODE_OF_CONDUCT.md).
