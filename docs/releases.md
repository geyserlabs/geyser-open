# Install and verify releases

The published SDK/CLI release is **0.1.0**. The **0.2.0 source preview** in this checkout is not a published artifact and is not a claim about running Cell/Agent software. Use the [source quickstart](quickstart.md) for the corrected local handler workflow.

Published artifacts are available from [PyPI](https://pypi.org/project/geyser-sdk/0.1.0/), [GitHub Releases](https://github.com/geyserlabs/geyser-open/releases/tag/v0.1.0), and the [Homebrew tap](https://github.com/geyserlabs/homebrew-tap). Pin exact versions, inspect the recorded distribution hashes, and use your normal lockfile workflow. A signature binds the expected publisher and exact bytes; a checksum without a trusted source does not authenticate the publisher.

Do not install 0.1.0 expecting the 0.2.0 execution or security corrections. Once a new release is published, read the changelog, verify its exact artifact, reauthenticate old CLI profiles, and check the live API and Agent readiness before remote use. Test the operations your integration needs, especially conditional decisions and typed results.

Published bytes are immutable. Corrections receive a new version. Security changes can revoke unsafe capability immediately. Report install problems with OS, Python version, install channel and safe error text; send suspected vulnerabilities through the security policy.
