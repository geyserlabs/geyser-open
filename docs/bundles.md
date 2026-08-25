# Agent Bundles and safe imports

An Agent Bundle selects persona, policy, skills, tools, connectors, evaluators, model profiles, and
runtime requirements by immutable reference. It is a declaration of desired bytes and capabilities,
not permission to activate them.

OpenClaw and Letta imports are treated as untrusted archives. Inspection is non-executing and
enforces compressed and expanded size limits, file-count limits, normalized relative paths, and
rejection of traversal, absolute paths, links, device files, nested archives, credentials, provider
sessions, and hidden reasoning. A person reviews the normalized selection before signing or staging.

```console
geyser init bundle careful-assistant
geyser validate careful-assistant
geyser package careful-assistant
```

Package creation is local. Signing, upload, staging, canary, and production promotion are distinct
steps with distinct scopes and retained evidence.
