# Authentication and projects

`geyser login` uses OAuth device authorization for a person. The CLI displays the Geyser origin
and a short user code, opens the authorization page when possible, and stores the resulting token
in the OS keychain. `--allow-file-credentials` is an explicit fallback that creates a 0600 file.
Tokens are never printed by ordinary commands.

CI uses a bounded service credential created for one customer/project with an expiry and narrow
scopes. Human and service credentials are not Agent keys. Tokens bind audience, customer,
project, scopes, Customer Cell assignment, expiry, and revocation. Available scopes are:

- `development:read`, `runs:read`, and `approvals:decide`;
- `packages:upload`, `packages:stage`, `packages:canary`, and `packages:promote`;
- `service:execute` for explicitly authorized project task creation.

`geyser logout` deletes the current profile credential. Authorization stays server-side; a local
`--yes` only suppresses the CLI confirmation and cannot bypass scope, policy, or approval.
