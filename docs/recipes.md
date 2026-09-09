# Reference applications

These examples ship in the **0.2.0 source preview**. Their local paths execute real sandboxed handlers. Remote paths require an upgraded, ready workspace and an active signed package.

## Apply an approved record change and recover without a duplicate write

```console
python examples/approved_record_update.py
```

This application example changes one synthetic ticket in a real temporary SQLite database. Its cases show rejection leaving the record untouched, approval advancing the version once, and a lost response being reconciled from the committed operation receipt. Repeating the same operation does not write again; a stale record version or changed request under the same operation ID fails.

Approval binds the run, tool, exact arguments, and operation identity. In production, keep the corresponding receipt in your system of record and inspect the actual result before resolving uncertainty. This example uses `LocalEmulator` for control flow and runs callbacks in your application process. It does not install a write-capable extension or demonstrate a remote Agent approval. Remote decisions use the customer approval APIs described in [durable execution](durable-runs.md).

## Normalize issue intake

```console
python examples/extension_app.py issue-normalizer
geyser test examples/packages/issue-normalizer
```

Input contains issue `number`, `title`, `body`, and `labels`; output has a stable `source_id`, trimmed text and a deterministic category. This is a useful adapter between your webhook receiver and a task system. Your application fetches the issue using its own authorized integration and supplies JSON. The handler never contacts GitHub or receives its credentials.

Provide a file with `--input issue.json`. The frozen cases check correct normalization and invalid issue identity.

## Reject unsupported citations before accepting an answer

```console
python examples/extension_app.py source-review-gate
geyser test examples/packages/source-review-gate
```

Supply known `source_ids` and claims, each with `text` and `source_ids`. The evaluator returns `passed` and zero-based `unsupported_claims`. It rejects missing or invented references and empty evaluations. It does not assess the truth of cited material.

Install this exact package using the [extension workflow](extensions.md), then run the same application remotely:

```console
python examples/extension_app.py source-review-gate   --remote-package YOUR_ACTIVE_PACKAGE_ID   --operation-id review:document-123:v1
```

Provide `GEYSER_API_URL` and `GEYSER_SERVICE_TOKEN` through your own secret manager. The application uploads owned JSON, submits an idempotent task, polls with a deadline and retrieves the typed result.

## Review supplied material with an Agent

Create `material.json` as an array of objects with `source_id` and `text`. Select a qualified Open Agent and use a service credential from the console:

```console
python examples/agent_review.py material.json --operation-id document-123:agent-review:v1
```

The example requests a summary and cited claims with limits of $1, 300 seconds, ten model requests and twenty tool calls. These are example ceilings, not a price quote or an estimate of actual provider cost. The Agent remains subject to workspace policy and human approvals. Inspect the returned run and apply the source-review gate to the output before accepting it.

A schema-valid answer is not necessarily a correct answer. Build application-specific critical cases from your real failure modes, and measure quality against a simpler direct-model or deterministic baseline.

## Support escalation investigator

`examples/support_escalation.py` chains both extensions with a qualified Open Agent. It normalizes a supplied ticket, asks the Agent to prepare an evidence-linked diagnosis and draft reply, then checks citation coverage. Each stage has a stable operation ID, so reconnecting with the same inputs resumes the existing tasks. The gate checks that cited source IDs exist; a human still judges whether the diagnosis is true and whether the reply should be sent.

After signing, uploading, and activating both reference packages in your project:

```sh
python examples/support_escalation.py \
  examples/packages/issue-normalizer/example-input.json examples/support-facts.json \
  --operation-id support-synthetic-42-v1 \
  --normalizer-package "$NORMALIZER_PACKAGE_ID" --review-package "$REVIEW_PACKAGE_ID"
```

Use your application's authorized ticket/account API to gather real records before submitting them. These packages do not receive external service credentials or fetch arbitrary URLs. The example produces a draft and never sends a customer message. The investigation has a $1 model-cost ceiling, ten provider requests and a 300-second elapsed limit; the two pure extension stages have 30-second limits and no model calls. Account compute/storage charges can be additional. Inspect the returned run IDs for observed usage and failures.
