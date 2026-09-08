# Security for developers

Report a suspected vulnerability privately to
[security@geyserlabs.ai](mailto:security@geyserlabs.ai). We acknowledge reports within two business
days and coordinate investigation, fixes, disclosure, and credit with the reporter.

Keep credentials, customer identifiers, private run content, and exploit details out of public
issues. See the [security policy](https://github.com/geyserlabs/geyser-open/blob/main/SECURITY.md)
for supported versions and reporting details.

## Credentials and project access

The CLI stores credentials in the OS keychain by default. Tokens are scoped, expiring, and
revocable, with an audience, customer, project, and Cell assignment. Use a separate bounded service
credential for CI. Read [authentication](authentication.md) before adding a remote integration.

## Actions and approvals

An approval binds a decision to the run, tool, arguments, and current state. An argument change or
stale binding requires a new decision. Stable idempotency keys let the server recognize a repeated
request; they must not be reused for a different intended action.

See [durable execution](durable-runs.md) for effects, unknown outcomes, and recovery.

## Packages and imports

Validate package contents before signing or staging. Archive inspection rejects unsafe paths,
links, and oversized contents. Imported Agent Bundles exclude credentials, provider sessions,
and hidden reasoning. A person reviews the selected components before activation.

The workspace remains responsible for granting capabilities. Installing a package does not give
it access to customer tools or data. Read [Agent Bundles](bundles.md) and
[release verification](releases.md).

## If something is compromised

Revoke affected credentials, stop using the affected package or runtime, and follow the security
advisory. Geyser can revoke capabilities and withdraw unsafe releases. Replacement packages use
new versions; published bytes are not silently replaced.
