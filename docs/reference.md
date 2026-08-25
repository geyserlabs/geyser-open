# Schema and API reference

The committed OpenAPI 3.1 document is `openapi/geyser-v1.openapi.json`. Individual generated JSON
Schemas are under `schemas/2026-08-24/`. `schemas/VERSION` names the current public contract.

Hand-designed SDK methods are the semantic interface; generated schemas are verification inputs,
not a substitute for safe retry, pagination, conditional decision, and authority behavior.
Run `make schemas` to detect drift.
