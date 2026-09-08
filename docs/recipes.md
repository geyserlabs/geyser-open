# Practical recipes

These examples give you a small, useful starting point. Local commands need no account; remote
commands use the project access established by [signing in](authentication.md).

## Validate a structured result

Suppose a tool must return a summary and a list of source URLs. Save this contract as `outcome.schema.json`:

```json
{
  "schema_version": 1,
  "schema_ref": "launch-summary",
  "schema_revision": "1",
  "json_schema": {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": [
      "summary",
      "sources"
    ],
    "additionalProperties": false,
    "properties": {
      "summary": {
        "type": "string",
        "minLength": 1
      },
      "sources": {
        "type": "array",
        "items": {
          "type": "string"
        }
      }
    }
  }
}
```

Save a candidate response as `result.json`:

```json
{"summary": "The guide is ready for review.", "sources": ["https://example.com/product-notes"]}
```

The contract names and versions the schema; `json_schema` describes the result itself. Then check it:

```console
geyser validate-outcome outcome.schema.json result.json
```

Remove `summary` and run the check again to see a failing result. Keep both valid and invalid
examples with your package. Read more about [structured outcomes](outcomes.md).

## Follow work from the terminal

```console
geyser login
geyser runs list
geyser runs watch YOUR_RUN_ID
```

Replace `YOUR_RUN_ID` with a run returned by `runs list`. To inspect its current state or export its
trace, use `geyser runs get YOUR_RUN_ID` or `geyser runs trace YOUR_RUN_ID`.

For an application that persists its own reconnect cursor, use the
[SDK event example](sdk.md#follow-a-run-through-reconnects).

## Inspect an Agent before choosing it

```console
geyser capabilities --agent YOUR_AGENT_NAME
```

Use an Agent name you can access. Read the capability response for the runtime and model you plan
to use; a framework name alone does not describe its supported operations. See
[compatibility](compatibility.md).

## Understand recovery after a tool call

Run the [local emulator example](quickstart.md#follow-a-complete-run), then inspect the sequence:
request, approval, tool start, recorded effect, checkpoint, completion.

If a real process stops after a tool has changed an external system but before it records the
result, the effect is **unknown**. Reconcile it against that system before deciding to retry.
An idempotency key identifies the same intended action; changing the arguments under that key is a
conflict. [Durable execution](durable-runs.md) describes the recovery model in detail.
