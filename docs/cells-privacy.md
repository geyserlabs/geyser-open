# Customer custody and transport

Every workspace runs on its own Customer Cell: a managed Cell, or a Host Cell on the customer’s own computer. The Cell owns developer projects, credential verifiers, task inputs/results, package bytes and run state. JSON objects and new package archives use its encrypted Data Home. Raw input/result bytes do not enter the Agent’s durable control spool. Global never holds a copy of this content, and a Cell never falls back to one.

Global sign-in bootstraps a human session and selects the current Cell. While a brand-new workspace’s Cell is still starting, requests get a “workspace is still being set up” answer instead; Global does not serve them in the meantime. The credential response includes an API URL bound to that Cell generation. Global’s developer relay forwards a project bearer unchanged, uses only registered active Cell routes, and does not exchange it for customer or Fleet authority. A changed generation requires authentication again.

**The compatibility relay processes plaintext content transiently.** TLS protects each network leg; this is not end-to-end encryption from your application to the Cell. Responses identify customer-cell custody and compatibility-relay transit. Storage location, relay transit, Agent compute and model/provider processing are separate choices.

Pure JSON extensions run without network or credential access. Open Agent tasks use the workspace’s configured model and tool routes, which can process authorized content outside the Cell. Moving compute to your hardware does not automatically move its data home or replace an external model provider.

When your code calls the workspace’s own models ([Use your own models](models.md)), prompts and answers travel through your Customer Cell to the Geyser Host computer running the model, and that computer sees them.

Retention follows the customer policy and excludes active task inputs. Agent deletion erases its owned developer objects and package records. Your integration must include its own downloads, logs, backups and result copies in its retention/deletion workflow. See [costs and limits](program.md) and the [privacy architecture](https://www.geyserlabs.ai/privacy-architecture).

Project erasure also removes its run streams and adapter checkpoints. An online Agent removes the marked developer task workspaces and Open session caches once its current Cell confirms that the project no longer belongs to it. Unavailable or changed routing defers local cleanup; offline Agents clean up when they reconnect. Revocation stops work but preserves retained records until erasure or the configured retention cutoff.
