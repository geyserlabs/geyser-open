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
| SDK/CLI 0.1.0b4 | yes | PyPI and GitHub Release | Python 3.11–3.13; clean macOS ARM64 and native Ubuntu AMD64 public installs passed | no | no |
| Developer API 2026-08-24 | yes | not public | Coordinator source gates passed | no | no |
| Manual signed CLI assets 0.1.0b4 | yes | GitHub Release | macOS ARM64 and native Ubuntu AMD64 checksum, provenance, signature, and execution gates passed | no | no |
| Homebrew formula | yes | pending | source gate passed; public tap install pending | no | no |

The `0.1.0b4` qualification receipt is the successful protected-tag
[release workflow](https://github.com/geyserlabs/geyser-open/actions/runs/32854732268) for source
commit `b105031a2de27633a183d82729b375168b138fcf`, followed by clean installs from PyPI and
execution of the downloaded standalone archives on Apple-Silicon macOS and native Intel
Ubuntu. All 16 retained Sigstore bundles verified against the exact protected workflow/tag
identity. Publication does not by itself enable a production API or deploy a developer runtime.
