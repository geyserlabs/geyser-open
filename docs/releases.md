# Geyser Open releases

A release publishes the SDK/CLI packages and the supported standalone binaries. The user's release
request is the authorization; no separate evidence or attestation approval is required.

## Release

1. Set the requested version and run `make check`.
2. Tag or dispatch the release workflow for that revision.
3. Build each published package/binary once.
4. Publish to PyPI/GitHub and update the Homebrew formula.
5. Run `geyser --json version` from one installed channel.
6. Yank/roll back the new version if the smoke fails.

Keep PyPI trusted publishing, package hashes, and any signature the installer actually verifies.
Do not require duplicate deterministic builds, SBOMs, SLSA/provenance bundles, per-file
attestations, a six-platform matrix, install/uninstall on every OS, or a retained release record.

Published versions remain immutable. A compromised release may be yanked and replaced by a new
version; do not overwrite an existing tag or package.
