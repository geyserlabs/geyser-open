# Security policy

Geyser Open is production software. Report suspected vulnerabilities privately to
**security@geyserlabs.ai**. Do not open a public issue containing exploit details, credentials,
customer identifiers, or tenant content. We acknowledge reports within two business days and
coordinate validation, remediation, disclosure, and credit with the reporter.

Supported security updates cover the current and previous minor SDK/CLI release. A security fix
may immediately narrow or revoke a capability; it never silently broadens authority. Credentials,
project scopes, Customer Cell assignment, runtime qualification, policy, and exact approval
bindings remain server-side controls.

See [docs/security.md](docs/security.md) for the threat model, artifact verification, compromise
response, revocation, and signing-key rotation procedures.
