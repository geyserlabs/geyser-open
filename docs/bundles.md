# Apply a bundle to one Agent task

The SDK/CLI 0.2.0 supports signed instruction packages on a qualified Open Agent advertising `bundle_tasks: true`. Select a package explicitly when creating a task. Installation alone does not change the Agent's shared persona or start work.

```console
geyser init agent-bundle careful-assistant
geyser validate careful-assistant
geyser package careful-assistant
```

Edit the generated `agent-bundle.json` before packaging. A bundle contains actual instructions and optional attributed context:

```json
{
  "schema_version": 1,
  "name": "careful-assistant",
  "persona": "Prepare concise reviews supported by the supplied sources.",
  "skills": [{
    "name": "review-facts",
    "description": "Check a proposed answer against its sources",
    "instructions": "Identify unsupported claims and return their source references."
  }],
  "context": [{
    "title": "Project terminology",
    "source": "example:project-notes:1",
    "kind": "notes",
    "content": "In this project, a completed review includes cited source IDs."
  }],
  "selection": {},
  "references": []
}
```

Sign, upload and activate the exact archive using the [package workflow](extensions.md). Configure the project's trusted publisher first. Wait for `active`, then use the returned package ID:

```sh
geyser tasks create --input review.json --bundle "$BUNDLE_PACKAGE_ID" \
  --idempotency-key review:document-123:v1 --max-cost 1 --max-seconds 300
```

The SDK equivalents are `TaskCreate(bundle_package_id=...)`, `skill_package_ids=[...]`, and `model_profile_package_id=...`. CLI `--skill PACKAGE_ID` is repeatable. These options require Agent execution and cannot be combined with a pure JSON handler's `--package` option.

## Contents and current authority

Persona and skill text become task-specific guidance. Context bodies are separate, attributed source material and are treated as untrusted input. They can carry exported notes, history or memory as text; they do not restore a live conversation, account or memory database. Instructions grant no tools, credentials or permissions and remain subject to current workspace policy.

Optional `selection` fields are `model_ref`, `model_profile_digest` and `policy_ref`. Each nonempty value must equal the currently qualified Agent selection. A mismatch stops execution with `bundle_reference_unavailable`; it never silently selects another model or weakens policy. Leave `selection` empty to use the current selection. A `model-profile` package requires both the exact model reference and profile digest; it cannot register a new provider or qualify a model.

A standalone `skill` package applies its actual `SKILL.md` body. `geyser validate` checks these text formats; `geyser test` executes JSON handlers and does not claim to evaluate instruction quality. Submit representative remote tasks and evaluate their outputs to test a skill's behavior.

Bundles allow up to 32 skills, 32 context entries and 32 references. Individual instruction/context bodies are bounded to 32 KiB; one bundle is bounded to 128 KiB and combined task packages to 256 KiB. Duplicate skill names across selected packages fail. Package permissions must be empty.

## What was applied

Inspect `client.get_run(run_id).run.execution["bundle_application"]`. It reports component kinds and content digests, resolved selection, and explicit omissions. Reference-only history, memory, artifact, deployment and relationship entries receive `reference_only_not_restored`. The report uses reference digests and does not copy context bodies into run metadata.

The Cell binds package identity, exact archive digest and assignment generations to the task. The Agent checks its verified copy against current assignments. Revocation or supersession stops affected work; retrying a task does not substitute a different package version. Publish a new version and submit a distinct task when changing instructions.

## Import boundary

The public format is the signed project ZIP containing `geyser-package.json` and the descriptor above. Public OpenClaw/Letta import, credential migration and conversion of first-party `.geyser-agent-bundle` exports are not implemented CLI features. To reuse permitted text, copy selected instructions or attributed context into this explicit format, review it, and sign the new package. Omit credentials and represent unrestored relationships as references. No archive inspection or listed reference is evidence that a source system was restored.
