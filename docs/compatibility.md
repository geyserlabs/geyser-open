# Compatibility and capability matrix

Developer Preview SDK/CLI 0.1 supports Python 3.11–3.13. The Python distributions are
platform-independent. Native CLI qualification targets macOS Apple Silicon and Ubuntu 24.04
AMD64; Windows is not yet a declared native target.

API v1 is additive and date-versioned `2026-08-24`. During preview, the current and previous SDK
minor are supported against the current server. Deprecations are documented for at least one
minor before removal unless a security issue requires immediate narrowing.

Runtime capability values are `native`, `geyser_emulated`, `unsupported`, or `forbidden` for an
exact framework/backend/adapter version/model profile/placement/privacy posture. Geyser Open is
the reference implementation, not a reason to overstate another adapter. The generated live
matrix and expiring qualification receipts are authoritative; this source table is explanatory.

| Surface | Implemented | Published | Qualified | Production enabled | Observed deployed |
|---|---:|---:|---:|---:|---:|
| SDK/CLI 0.1.0b2 source | yes | no | macOS ARM64 and Ubuntu AMD64 release gates passed | no | no |
| Developer API 2026-08-24 | yes | not public | Coordinator source gates passed | no | no |
| Homebrew/manual assets | source workflow pending W14 | no | no | no | no |
