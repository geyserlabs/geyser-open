# Releases

This documentation targets **SDK/CLI 0.2.0**. The [GitHub release](https://github.com/geyserlabs/geyser-open/releases/tag/v0.2.0) lists its exact source tag, standalone downloads, public contracts and distribution checksums. [PyPI SDK](https://pypi.org/project/geyser-sdk/0.2.0/), [PyPI CLI](https://pypi.org/project/geyser-open/0.2.0/) and the [Homebrew tap](https://github.com/geyserlabs/homebrew-tap) are separate publication channels. Check the installed version with `geyser --json version`; do not assume a channel has updated just because source was merged.

If the matching release is not available, this checkout is unreleased source. Use the [source quickstart](quickstart.md) for local development. Hosted versioned documentation is published only from an existing matching release tag.

Pin exact versions, inspect the recorded distribution hashes, and use your normal lockfile workflow. A signature binds the expected publisher and exact bytes; a checksum without a trusted source does not authenticate the publisher.

SDK/CLI 0.1.0 does not include the 0.2.0 execution and reliability corrections. Read the [changelog](changelog.md), reauthenticate old CLI profiles, and check [live API and Agent readiness](compatibility.md) before remote use. A package installation does not upgrade your Customer Cell or Agent. Verify the operations your integration needs, especially conditional decisions and typed results.

## Publish matching documentation

Maintainers dispatch **Publish developer documentation** from the exact `v0.2.0` tag with version `0.2.0`, after its GitHub release is published. The workflow checks the tag, checkout SHA, SDK/CLI versions and release state before updating the versioned site and stable alias. A dispatch from `main` or with a mismatched version is rejected.
