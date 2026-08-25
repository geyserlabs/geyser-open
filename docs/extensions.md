# Extensions, specialists, and Agent Bundles

`geyser init` creates skills, connectors, tools, evaluators, model profiles, or Agent Bundle
selection manifests. Each declares the narrowest requested permissions and frozen success/denial
cases. Declarations request capabilities; they do not grant them.

Specialists are durable child runs with bounded concurrency, depth, budget, and authority. Their
typed results return through the parent run. Importing an OpenClaw or Letta artifact treats it as
untrusted data: archives are size-bounded, traversal and links are rejected, code is not executed
during inspection, credentials/provider sessions/hidden reasoning are excluded, and an owner
reviews the selection before activation.
