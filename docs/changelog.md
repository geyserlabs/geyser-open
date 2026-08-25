# Changelog

## 0.1.0b4 — Developer Preview

The `v0.1.0b1` workflow stopped before publication because its hidden
standalone-artifact directory was excluded from upload. No package or release
was published from that tag. The `v0.1.0b2` workflow reached keyless signing
but stopped before publication when the job's Python selector overrode the
Sigstore action's isolated environment. No package or release was published
from that tag either.

The `v0.1.0b3` workflow completed signing and attestations but stopped before
publication because an orphaned PyPA action revision referenced a container
image that no longer existed. No package or release was published from that
tag.

- Public, platform-independent Python SDK with synchronous and asynchronous clients.
- Public CLI for local scaffolding, validation, emulator testing, package lifecycle, durable-run
  inspection, approvals, capability discovery, and OAuth login.
- Frozen API `2026-08-24`, JSON Schemas, OpenAPI 3.1, emulator, examples, and conformance fixtures.
- Standalone Apple-silicon macOS and Ubuntu 24.04 AMD64 CLI artifacts.
- Reproducible builds, checksums, Sigstore bundles, GitHub SLSA provenance, SPDX and CycloneDX
  SBOMs, and canonical PyPI/GitHub/Homebrew channels.

This is a preview contract. Implemented, published, qualified, production-enabled, and observed
deployed status remain separate in the [compatibility matrix](compatibility.md).
