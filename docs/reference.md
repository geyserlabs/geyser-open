# API and schema reference

The SDK provides convenient typed operations. The OpenAPI document and JSON Schemas describe the
underlying contracts when you need request fields, response shapes, or another language client.

## OpenAPI

- [Live Developer API](https://agents.geyserlabs.ai/api/v1/openapi.json)
- [Committed OpenAPI 3.1 document](https://github.com/geyserlabs/geyser-open/blob/main/openapi/geyser-v1.openapi.json)

The current public contract is **2026-08-24**. Use [authentication](authentication.md) to connect to
protected endpoints and [compatibility](compatibility.md) to understand version support.

## JSON Schemas

[Browse the generated schemas](https://github.com/geyserlabs/geyser-open/tree/main/schemas/2026-08-24)
for task, run, event, approval, package, and related models.

When validating application output, start with [structured outcomes](outcomes.md). For retries,
pagination, and decisions that depend on current state, use the [SDK](sdk.md) rather than treating
a generated HTTP client as the complete execution model.

## Working on Geyser Open

From a source checkout with its development dependencies installed, run `make schemas` to check
that committed schemas match the SDK models. See the
[repository](https://github.com/geyserlabs/geyser-open) for contribution and build instructions.
