# Releases and supply-chain trust

Geyser Open has three deliberately separate public authorities:

- PyPI is authoritative for the platform-independent `geyser-sdk` and
  `geyser-open` Python distributions.
- GitHub Releases is authoritative for manual downloads, frozen schemas,
  OpenAPI, SBOMs, checksums, signatures, and provenance.
- `geyserlabs/homebrew-tap` is authoritative for the polished standalone CLI.

Every release is triggered only by a version tag that resolves to the exact
protected `main` commit. The workflow rejects a mismatched package version, a
dirty checkout, or a tag on any other commit. Python distributions and both
supported standalone archives are built twice and must be byte-identical. The
only qualified standalone targets are Apple-Silicon macOS and AMD64 Linux.

## Install the same release through every channel

Pin the Developer Preview version when validating a deployment:

```console
python -m pip install geyser-sdk==0.1.0b2 geyser-open==0.1.0b2
uv tool install geyser-open==0.1.0b2
pipx install geyser-open==0.1.0b2
brew tap geyserlabs/tap
brew install geyser
```

For a manual install, download the archive for `darwin-arm64` or `linux-amd64`
from the GitHub Release, verify it as below, extract `geyser`, and place it on
`PATH`. Each channel must report the same value from `geyser --json version`.

## Verify a manual download

Download the artifact, its `.sigstore.json` bundle, and `SHA256SUMS` from the
same GitHub Release. Then run:

```console
sha256sum --check SHA256SUMS --ignore-missing
gh attestation verify geyser-open-*.tar.gz --repo geyserlabs/geyser-open
python -m sigstore verify identity \
  --bundle geyser-open-*.tar.gz.sigstore.json \
  --cert-identity-regexp 'https://github.com/geyserlabs/geyser-open/.github/workflows/release.yml@refs/tags/v' \
  --cert-oidc-issuer https://token.actions.githubusercontent.com \
  geyser-open-*.tar.gz
```

The release record contains the exact source commit and workflow URL. SPDX and
CycloneDX SBOMs, a lockfile-derived dependency inventory, SLSA provenance, and
signed SBOM attestations are retained with the artifacts. GitHub Actions are
pinned to immutable commits; publication uses short-lived OIDC identities and
does not use a stored PyPI token or signing key.

PyPI publication is project-scoped. The `geyser-sdk` trusted publisher uses
the `pypi` GitHub environment, while `geyser-open` uses
`pypi-geyser-open`; both identities are bound to `.github/workflows/release.yml`.
The release workflow uploads each project's distributions in its own job so a
credential minted for one project is never reused for the other.

## Rollback, yank, and revocation

Released bytes are immutable. A defect is corrected in a new version; an
existing tag or GitHub asset is never replaced. Maintainers may yank a PyPI
release to prevent new unconstrained resolution while preserving reproducible
installs. A yanked version remains documented with its digest and reason.

For a compromised release, maintainers must immediately:

1. make the GitHub Release unavailable and yank both PyPI projects with the
   same reason;
2. disable the PyPI trusted-publisher binding and GitHub release environment;
3. remove or disable the affected Homebrew formula version;
4. publish a signed security advisory identifying versions, hashes, source
   commit, exposure, and remediation;
5. audit workflow and repository changes, then restore trust only through a
   reviewed workflow commit and a fresh release version.

Signing is keyless: each release receives a short-lived Sigstore certificate
bound to the protected workflow identity. “Key rotation” therefore means
rotating or revoking the trusted OIDC identity—workflow path, repository,
environment, or issuer—and updating PyPI and verification policy together.
Historic Rekor entries and retained bundles remain verifiable. If the workflow
identity itself is suspect, consumers must treat every artifact issued during
the published incident window as revoked, regardless of a valid signature.

Report suspected compromise privately through the process in `SECURITY.md`.
