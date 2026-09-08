# Structured outcomes

An outcome schema turns a successful-looking response into a testable contract. Use Draft 2020-12
JSON Schema inside a versioned contract with `schema_version`, `schema_ref`, and `json_schema`.
External `$ref` values are rejected. Keep both valid and invalid result fixtures in source.
The [structured-result recipe](recipes.md#validate-a-structured-result) includes a complete contract
and result you can copy.

```console
geyser validate-outcome outcome.schema.json result.json
```

At runtime, Geyser records the schema digest with the run. A valid response completes with its typed
value. An invalid response may enter a bounded repair loop if policy allows. Exhausted repair ends in
an explicit terminal failure; it never silently converts malformed output into success.

Input declarations are strict because an unknown field could request new authority. Output models
preserve additive server fields so an older client can observe a newer API without discarding
evidence.
