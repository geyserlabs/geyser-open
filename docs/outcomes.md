# Typed outcomes

Upload an outcome contract as `InputCreate(kind="outcome_contract", value=...)`, then use the returned reference in `TaskCreate.outcome_contract_ref`. The Cell verifies project ownership, binds the exact reference at admission and validates the committed result.

A contract has `schema_version: 1`, a stable `schema_ref`, optional `schema_revision`, and a Draft 2020-12 `json_schema`. Public executable schemas are self-contained: references (`$ref`, `$dynamicRef`, `$id`) and regular-expression validation are not accepted. Schema depth and node count are bounded. Keep schemas small and explicit.

The SDK’s local `normalize_contract` and `validate_outcome` helpers also support existing standalone contracts. A locally valid schema may use features intentionally excluded at the remote execution boundary; uploading it is the authoritative compatibility check.

Inputs and results are limited to 1 MiB remotely. A schema-valid answer can still be wrong. Use independent evidence and application-specific evaluators; the source-review reference application checks citation coverage only. No hidden reasoning is required or exposed.
