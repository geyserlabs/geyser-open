# Changelog

This project follows Semantic Versioning. Developer API compatibility is tracked separately by
the date-versioned schema/API contract.

## 0.1.0b4 — Developer Preview

`v0.1.0b4` was published from protected `main` commit
`b105031a2de27633a183d82729b375168b138fcf` to both PyPI projects and GitHub Releases. Its
platform-independent distributions, macOS ARM64 and Linux AMD64 standalone archives, checksums,
SBOMs, provenance, PyPI attestations, and keyless Sigstore bundles passed the release workflow and
clean consumer qualification. Homebrew publication and production enablement are tracked
separately.

The `v0.1.0b1` release attempt stopped before publication when its hidden
standalone-artifact directory was excluded from upload. No PyPI project or
GitHub Release was created from that tag. The `v0.1.0b2` attempt reached the
keyless-signing stage but stopped before publication when the job's configured
Python selector overrode the Sigstore action's isolated environment. No PyPI
project or GitHub Release was created from that tag either.

The `v0.1.0b3` attempt completed signing and attestations but stopped before
publication because an orphaned PyPA action revision referenced a container
image that no longer existed. No PyPI project or GitHub Release was created
from that tag.

- Independent typed sync/async `geyser-sdk` with problem-details errors, bounded safe retries,
  pagination, cancellation, reconnecting event watch, and exact capability evidence.
- Credential-free deterministic emulator with durable crash injection, checkpoints,
  deterministic models/tools, exact approval binding, and structured outcomes.
- `geyser` CLI with scaffold, validate, test, dev, package, sign, lifecycle, run, approval,
  capability, OAuth, and diagnostic commands.
- Versioned JSON Schemas, OpenAPI, examples, conformance fixtures, and release controls.
