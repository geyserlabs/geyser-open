# Changelog

This project follows Semantic Versioning. Developer API compatibility is tracked separately by
the date-versioned schema/API contract.

## 0.1.0b4 — Developer Preview

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
