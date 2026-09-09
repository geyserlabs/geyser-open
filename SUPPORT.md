# Developer support and maintenance

Geyser engineering owns the Python SDK, CLI, public API documentation, and reference applications in this repository. GitHub Issues is the supported integration-help and bug-report channel. Include versions, expected behavior, a small synthetic example, and a safe error code. Never post credentials or private workspace content.

During the preview, our operational targets are an initial response within two business days and a triage update within five business days, excluding US holidays. These are service targets, not a contractual response-time or availability SLA. Acknowledgement does not promise a resolution date. We will update unresolved issues when their priority or workaround changes.

The current published minor release receives correctness fixes, documentation corrections, and dependency maintenance. Use its newest patch release. Source previews require the documented matching server and Agent versions; a source merge alone does not update a deployed workspace.

For planned breaking public API changes, publish a migration guide and provide at least 90 days of notice when feasible. Urgent fixes that remove unsafe access can take effect sooner. Never silently rewrite a published package version. Changelogs distinguish source changes, released packages, and required runtime changes.

Report sensitive issues through [the security policy](SECURITY.md). Review the targets against actual support workload monthly. The initial owner is the Geyser engineering maintainer team; record ownership transfers here so developers retain a durable contact point.
