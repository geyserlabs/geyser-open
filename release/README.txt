Geyser Open standalone CLI
==========================

The `geyser` executable in this archive is the framework-neutral Geyser
developer CLI. Download the archive and SHA256SUMS from the same exact version
at https://github.com/geyserlabs/geyser-open/releases before installing it.

Compare its SHA-256 digest with SHA256SUMS from the same GitHub Release. The
Homebrew tap performs the digest check automatically.

Remote API commands and local package validation/creation do not require a
separate Python installation. Executing Python extensions with `geyser test`
or `geyser dev` requires an installed Python 3.11 or newer on your normal PATH,
outside the package and current directory. macOS requires sandbox-exec; Linux
requires bubblewrap with working user namespaces. Missing prerequisites cause
an explicit failure; packages never run without the required isolation.

Documentation: https://geyserlabs.ai/developers
Security: https://github.com/geyserlabs/geyser-open/security/policy
Publication recovery
--------------------
PyPI trusts release.yml in the existing pypi environment for geyser-sdk and
pypi-geyser-open for geyser-open. Keep each exact environment on its project
job; it is part of the publisher identity. A retry skips an existing upload
only when both published file hashes match the original verified artifacts.

If builds complete but publication stops, reuse the original run's
complete-release artifact. Do not rebuild or move the package release tag.
After merging any workflow correction, create a separate immutable tag such as
v0.2.0-publish-20260909 at that reviewed merge. This is a workflow tag, not a
new package version. It matches the existing tag-only environment policy and
does not trigger a new build. Dispatch release.yml from that tag with version
0.2.0 and reuse_run_id set to the original release run. The workflow checks
the original build against v0.2.0 and validates every artifact before upload.
