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
