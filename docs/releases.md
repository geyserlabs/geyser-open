# Install and verify a release

Geyser Open publishes the Python SDK, Python CLI, and standalone CLI builds through public channels.
The current stable release is **0.1.0**.

## Python packages

```console
python -m pip install geyser-sdk==0.1.0 geyser-open==0.1.0
geyser --json version
```

Package pages:

- [geyser-sdk on PyPI](https://pypi.org/project/geyser-sdk/0.1.0/)
- [geyser-open on PyPI](https://pypi.org/project/geyser-open/0.1.0/)

PyPI lists each distribution's hashes and publishing details. Pin the version in your application
and use your normal lockfile workflow to keep installations reproducible.

## Homebrew and standalone CLI

```console
brew tap geyserlabs/tap
brew install geyser
geyser --json version
```

The [Homebrew formula](https://github.com/geyserlabs/homebrew-tap) records the selected release
and archive hashes. Manual downloads are on the
[0.1.0 GitHub Release](https://github.com/geyserlabs/geyser-open/releases/tag/v0.1.0), alongside
checksums and signing information. Choose the archive for your platform and verify it against the
release's published checksum before installation.

## Upgrading

Read the [changelog](changelog.md), check [compatibility](compatibility.md), and update your pinned
version. Test the operations your application uses, especially structured results and decisions
that depend on current run state.

Published versions are immutable. If a release is withdrawn, follow the advisory and install its
replacement or a supported previous version. A replacement uses a new version number.

## Report a release problem

Report installation problems in [GitHub Issues](https://github.com/geyserlabs/geyser-open/issues),
including your OS, Python version, install channel, and the error text. Remove credentials and
private content first. Send suspected vulnerabilities to
[security@geyserlabs.ai](mailto:security@geyserlabs.ai).
