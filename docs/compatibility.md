# Compatibility and capability matrix

Production SDK/CLI 0.1 supports Python 3.11–3.13. The Python distributions are
platform-independent. Native CLI qualification targets macOS Apple Silicon and Ubuntu 24.04
AMD64; Windows is not yet a declared native target.

API v1 is additive and date-versioned `2026-08-24`. The current and previous SDK
minor are supported against the current server. Deprecations are documented for at least one
minor before removal unless a security issue requires immediate narrowing.

Runtime capability values are `native`, `geyser_emulated`, `unsupported`, or `forbidden` for an
exact framework/backend/adapter version/model profile/placement/privacy posture. Geyser Open is
the reference implementation, not a reason to overstate another adapter. The generated live
matrix and expiring qualification receipts are authoritative; this source table is explanatory.

| Surface | Implemented | Published | Qualified | Production enabled | Observed deployed |
|---|---:|---:|---:|---:|---:|
| SDK/CLI 0.1.0 | yes | PyPI and GitHub Release | Python 3.11–3.13; clean macOS ARM64 and native Ubuntu AMD64 public installs passed | yes | canonical public channels |
| Developer API 2026-08-24 | yes | [public HTTPS OpenAPI](https://agents.geyserlabs.ai/api/v1/openapi.json) | Protected contract/source, customer-1 shared-runtime, fleet, and live unauthenticated-denial gates passed; owner-waived independent validation remains optional | Production and GA routes yes | Global and customer-1 managed Cell at Coordinator source `ee341285efa1a067555c83be2130926f755f41e9` / image `sha256:e275d5e58f6c256ecd7bf3acac600b04c10e8e25f7468888b605dbd04e84b297` |
| Manual signed CLI assets 0.1.0 | yes | GitHub Release | macOS ARM64 and native Ubuntu AMD64 checksum, provenance, signature, and execution gates passed | yes | canonical GitHub Release |
| Homebrew formula 0.1.0 | yes | `geyserlabs/homebrew-tap` | Apple-Silicon public tap install, test, and audit passed; native Ubuntu AMD64 formula generation and integrity gates passed | yes | canonical public tap |
| SDK/CLI 0.1.0b4 | yes | PyPI and GitHub Release | prior beta qualification receipt retained | no | superseded by 0.1.0 |

The `0.1.0b4` qualification receipt is the successful protected-tag
[release workflow](https://github.com/geyserlabs/geyser-open/actions/runs/32854732268) for source
commit `b105031a2de27633a183d82729b375168b138fcf`, followed by clean installs from PyPI and
execution of the downloaded standalone archives on Apple-Silicon macOS and native Intel
Ubuntu. All 16 retained Sigstore bundles verified against the exact protected workflow/tag
identity. The stable release is rebuilt and re-signed from its own protected `v0.1.0` source tag;
the beta receipt is retained as prior qualification evidence, not reused as the stable artifact
identity.

The Developer API deployment receipt is Cloud Build
`844f8123-f853-4c59-bdbc-a364da4d2517`, which produced the immutable Coordinator image above
from the recorded clean merged source. The live OpenAPI document reports title
`Geyser Developer API`, version `2026-08-24`, and the unauthenticated capabilities route denies
access with HTTP 401. Those observations establish publication, deployment, and fail-closed
authentication. The product owner waived the independent non-implementer exercise as a mandatory
release gate on 2026-08-25. The [optional independent validation](external-preview.md) remains
public, and no independent receipt is claimed.

The Homebrew qualification receipt is public-tap commit
`977a2ac9e5cb764dda97e0614b09de76dbbfaa31` and its successful
[merged-main workflow](https://github.com/geyserlabs/homebrew-tap/actions/runs/32857989721).
