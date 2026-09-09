# Signed JSON extensions

Executable extensions in the **0.2.0 source preview** are synchronous Python handlers that accept one JSON value and return one JSON value. `tool`, `connector`, and `evaluator` share this contract. Their effect class is `pure`: no network, host files, subprocesses, inherited credentials, or external side effects.

## Package contract

A package contains `geyser-package.json`, a kind-specific descriptor (`tool.json`, `connector.json`, or `evaluator.json`), the handler, and `evals/cases.json`.

```json
{
  "schema_version": 1,
  "name": "word-count",
  "description": "Count words in supplied text.",
  "handler": "handler.py:run",
  "effect_class": "pure",
  "input_schema": {"type": "object", "required": ["text"], "properties": {"text": {"type": "string"}}, "additionalProperties": false},
  "output_schema": {"type": "object", "required": ["word_count"], "properties": {"word_count": {"type": "integer"}}, "additionalProperties": false}
}
```

```python
def run(value):
    return {"word_count": len(value["text"].split())}
```

The manifest name must match the descriptor. Permissions must be empty. The handler path must remain inside the package. Use the standard library; dependency installation and arbitrary build/install hooks are not supported.

Frozen cases require `input` and exactly one `expected_output` or `expected_error`, with at least one critical case. `geyser test` actually invokes each handler and checks the result. A label saying “expected success” is not a test.

## Isolation and bounds

Code is imported only after OS isolation is active. Linux uses bubblewrap user/process/network namespaces and a syscall filter denying process creation, execution, networking and namespace escape. macOS uses a deny-by-default sandbox profile. There is no unsandboxed fallback.

Each invocation accepts/returns at most 1 MiB of JSON, runs for at most 30 seconds, and has bounded output, CPU and file descriptors. Linux applies an address-space limit. macOS applies a sampled RSS watchdog; this is not a hard kernel allocation ceiling. Temporary writes are private and removed after execution. The package is copied through directory handles that refuse symlink traversal. Archive paths, special files, links and size bounds are validated again on the Agent.

Packages are limited to 512 entries, 2 MiB per file and 10 MiB unpacked. Installation runs 1–32 frozen cases with at most two seconds per case and ten seconds total. Keep installation cases fast and deterministic. At most 200 desired packages may be assigned to an Agent.

## Trust, stage, install

1. In **Developers**, configure the exact trusted certificate identity and OIDC issuer for the project. For GitHub Actions, use the exact workflow certificate identity and `https://token.actions.githubusercontent.com`. For an interactive Sigstore identity, use its actual certificate identity and issuer; do not copy a GitHub issuer onto a personal identity.
2. Install the Sigstore CLI and sign the exact archive with `geyser sign ARCHIVE`. Never modify the archive after signing.
3. Login with the required package scopes and upload:

```console
geyser publish ARCHIVE --stage --signature-bundle BUNDLE
geyser promote PACKAGE_ID --digest SHA256_DIGEST --canary
geyser status
```

The Cell cryptographically verifies the archive, certificate, issuer and transparency bundle against the administrator’s trust configuration. Supplied `verified: true` metadata has no authority.

Promotion creates `pending_install`. The assigned Agent verifies the exact bytes again, executes the frozen cases inside the sandbox, and acknowledges the package digest, publisher generation, Cell generation and installation generation. Only a matching successful acknowledgement produces `active`. Failed installation is visible as `install_failed`; it is not executable. Existing unverified records are shown as `unverified`.

“Canary” selects this project’s assigned Agent; it is not a fleet-wide deployment cohort. `geyser promote ... --production` changes the same project’s stage and requires another installation acknowledgement. No other customer gains the package. The prior active version remains available while a new candidate installs; successful activation supersedes it. An older pending acknowledgement cannot replace the newer candidate.

## Revoke and recover

`geyser revoke PACKAGE_ID --digest SHA256_DIGEST` removes assignment authority. Replacing publisher trust revokes prior verification generations; re-upload/re-promote verified bytes after reviewing the new identity. Revoking the project removes all package authority. The Agent rechecks current assignment before every execution, so a local archive cache cannot restore revoked authority.

If installation fails, inspect `status`, verify publisher settings and sandbox availability, correct the package under a new version, and promote again. A repeated promotion ID identifies the same decision; use a new ID for a deliberate new installation attempt. Local validation alone does not activate an Agent package.

## Configuration previews

`skill`, `model-profile`, and `agent-bundle` scaffolds support validation and packaging only. They are not installed or executed by the public JSON package consumer. Imported third-party runtimes, arbitrary connectors with credentials, and provider/model registration are not supported public extension features.

## Supported JSON Schema subset

Input/output and task outcome schemas use bounded validation. Supported constraints are `type`, `properties`, `required`, `additionalProperties`, `items`, `prefixItems`, `minItems`, `maxItems`, `minLength`, `maxLength`, `minimum`, `maximum`, `exclusiveMinimum`, `exclusiveMaximum`, `minProperties`, `maxProperties`, scalar `const`, and `enum` with at most 32 scalar values. Descriptive `title`, `description`, `$schema`, `default`, and `examples` are allowed. Unknown keywords fail validation; references, regex/format validation, combinators, `contains` and `uniqueItems` are unavailable.

Schemas allow at most 512 nodes, depth 24, and 4,096 characters per schema string. JSON data allows at most 10,000 nodes and depth 24, within the 1 MiB input/output byte limit. Numeric magnitudes must be finite and at most 1e100. Validation has a 50,000-operation budget, a one-second ceiling, and checks the invocation's remaining deadline and cancellation. Handler execution uses that same remaining invocation deadline. These limits apply during package qualification and Agent execution; the Cell applies them again to results.
