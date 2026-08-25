# Geyser Developer Preview

Geyser is a framework-neutral control plane for durable agentic work. The public SDK talks to a
versioned API; it is not an Agent runtime and does not include or grant a model, brain, provider,
browser, tool, credential, policy, or deployment authority.

Start with the [five-minute emulator quickstart](quickstart.md), then read
[authentication and projects](authentication.md), [SDK clients](sdk.md), and the
[CLI reference](cli.md). Exact implemented, published, qualified, production-enabled, and
observed-deployed status is recorded separately in the [compatibility matrix](compatibility.md).

Release consumers should also read [release verification and supply-chain
trust](releases.md), including the immutable-artifact, yank, compromise, and
revocation policy.

## Public authorities

- [GitHub](https://github.com/geyserlabs/geyser-open) — source, examples, conformance, and releases.
- [PyPI SDK](https://pypi.org/project/geyser-sdk/) and
  [PyPI CLI](https://pypi.org/project/geyser-open/) — Python distribution authority.
- [Homebrew tap](https://github.com/geyserlabs/homebrew-tap) — standalone CLI authority.
- [Compatibility status](compatibility.md) — implemented, published, qualified,
  production-enabled, and observed-deployed facts.

!!! warning "Developer Preview"

    Version 0.1.0b4 supports Python 3.11–3.13. Standalone qualification is limited to
    Apple-silicon macOS and Ubuntu 24.04 AMD64. A local emulator pass does not grant production
    capability or authority.
