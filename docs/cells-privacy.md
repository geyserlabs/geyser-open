# Customer custody and transport

The Customer Cell owns developer projects, credential verifiers, task inputs/results, package bytes and run state. In a dedicated Cell, JSON objects and new package archives use its encrypted Data Home. Raw input/result bytes do not enter the Agent’s durable control spool. Legacy monolith installations retain their existing local storage boundary; a dedicated Cell does not silently fall back to a Global content copy.

Global sign-in bootstraps a human session and selects the current Cell. The credential response includes an API URL bound to that Cell generation. Global’s developer relay forwards a project bearer unchanged, uses only registered active Cell routes, and does not exchange it for customer or Fleet authority. A changed generation requires authentication again.

**The compatibility relay processes plaintext content transiently.** TLS protects each network leg; this is not end-to-end encryption from your application to the Cell. Responses identify customer-cell custody and compatibility-relay transit. Storage location, relay transit, Agent compute and model/provider processing are separate choices.

Pure JSON extensions run without network or credential access. Open Agent tasks use the workspace’s configured model and tool routes, which can process authorized content outside the Cell. Moving compute to your hardware does not automatically move its data home or replace an external model provider.

Retention follows the customer policy and excludes active task inputs. Agent deletion erases its owned developer objects and package records. Your integration must include its own downloads, logs, backups and result copies in its retention/deletion workflow. See [costs and limits](program.md) and the [privacy architecture](https://www.geyserlabs.ai/privacy-architecture).
