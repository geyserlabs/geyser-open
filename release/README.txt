Geyser Open standalone CLI
==========================

The `geyser` executable in this archive is the framework-neutral Geyser
developer CLI. Verify the archive before installing it:

  gh attestation verify <archive> --repo geyserlabs/geyser-open
  python -m sigstore verify identity \
    --bundle <archive>.sigstore.json \
    --cert-identity-regexp 'https://github.com/geyserlabs/geyser-open/' \
    --cert-oidc-issuer https://token.actions.githubusercontent.com \
    <archive>

Compare its SHA-256 digest with SHA256SUMS from the same GitHub Release. The
Homebrew tap performs the digest check automatically.

Documentation: https://geyserlabs.ai/developers
Security: https://github.com/geyserlabs/geyser-open/security/policy
