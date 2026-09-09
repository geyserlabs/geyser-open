# Developer security

Report suspected vulnerabilities privately to [security@geyserlabs.ai](mailto:security@geyserlabs.ai), following the repository’s [security policy](https://github.com/geyserlabs/geyser-open/blob/main/SECURITY.md). Do not include credentials, customer content or exploit details in a public issue.

## Enforced boundaries

- Human grants require current membership, role and Agent assignment; expired, revoked or moved grants fail closed.
- Project credentials remain bound to one project, Agent, Cell and audience. Fleet sessions cannot read the customer developer API. Service credentials do not impersonate a person’s decision authority.
- SDK/CLI HTTP destinations allow HTTPS or exact loopback development hosts. A stored credential cannot be silently redirected to another API origin or path.
- Signed packages must match an administrator-configured certificate identity and issuer, their exact archive digest and the current publisher generation. Both Cell and Agent verify cryptography; metadata flags are not evidence.
- Executable handlers start inside a supported OS sandbox before import. No ambient credentials, networking, host files or subprocesses are granted. Missing sandbox support disables execution.
- Task claims and package acknowledgements bind exact current generations; late processes cannot reactivate revoked authority or overwrite another owner’s result.
- Inputs, contracts and results are project-owned, bounded and validated. Public schemas reject references and regex features that could introduce unbounded remote resolution or validation work.

## Compromise response

Revoke the affected credential or project in the console. Revoke an installed package with its expected digest. If publisher identity changes, update trust, review/sign the new bytes and explicitly promote again. Stop affected runs using a current owner/admin credential. Already committed external effects require domain-specific reconciliation.

A software release, local test pass or valid signature does not establish that code is free of defects. Test critical behavior with synthetic fixtures and keep your application’s own permission, secret-storage and review controls. The in-memory emulator executes your registered callbacks in your process; only the executable extension path supplies the OS sandbox.
