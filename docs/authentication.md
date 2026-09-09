# Projects, login and service credentials

The **0.2.0 source preview** needs a matching Cell and Agent rollout for remote work. Use the console’s **Developers** page to see execution readiness. An unavailable Agent is not made executable by creating a project.

## Create a project

1. Sign into your customer workspace as an owner or administrator and open **Developers**.
2. Create a project and select its Agent. Each project has one assigned Agent.
3. For application execution, create a short-lived **service credential** with “Submit tasks and read results”. Save the token in your application’s secret manager and copy its **API URL**. The token is shown once.
4. Use the returned API URL exactly. It includes the current Cell generation. A different origin or generation requires fresh authentication.

The Global sign-in origin bootstraps access and selects the Customer Cell. It does not mint a customer session from a project bearer. The Cell owns the project credential and checks its audience, customer, project, Agent, expiry, revocation, and current assignment on every use.

## Interactive CLI login

```console
geyser login
geyser doctor
geyser capabilities
```

Compare the short device code and review the project and scopes in the browser before approving. The CLI saves the issued API URL with the credential in the OS keychain. It refuses to send that credential to a different destination. Old profiles without an origin must log in again.

Owners/admins can request additional scopes when needed:

```console
geyser login --scope development:read --scope runs:read --scope runs:manage --scope approvals:decide
```

For package work, request `packages:upload`, `packages:stage`, `packages:canary`, and, only when needed, `packages:promote`. Member grants require a current Agent assignment. Removing a member, changing their role, revoking the project, or changing Cell assignment invalidates their old grant. A service credential belongs to the project and has its own lifecycle.

## CI and applications

Use `GEYSER_API_URL` and a token provided by your secret manager. Never put a token in a command argument, repository, browser storage, example, or issue report. The CLI accepts a service token on standard input:

```console
# Have your secret manager pipe the token into this command.
geyser --api-url YOUR_ISSUED_API_URL login --service-token-stdin
```

`--allow-file-credentials` explicitly opts into a local, user-owned, mode-0600 fallback when the OS keychain is unavailable. Prefer the keychain. `geyser logout` removes the local copy; it does not revoke an already copied remote token. Revoke tokens in the console.

## Scope boundaries

| Grant | Intended use |
|---|---|
| `service:execute` | Upload owned JSON, submit tasks and read their results |
| `development:read`, `tasks:read` | Read project task/development state |
| `runs:read`, `traces:read` | Inspect project runs and traces |
| `capabilities:read` | Read the assigned Agent’s execution and runtime capabilities |
| `runs:manage`, `approvals:decide` | Current customer owner/admin decisions; service credentials cannot impersonate a person |
| `packages:upload`, `packages:stage` | Upload/stage signed bytes |
| `packages:canary`, `packages:promote` | Owner/admin activation authority |

Agent keys produce runtime events; Fleet sessions operate the physical fleet. Neither is a substitute for a developer credential. The current OAuth client is the Geyser CLI; arbitrary third-party OAuth client registration is not offered. Device flow and loopback PKCE use single-use grants. Token and device-code endpoints accept JSON and standard URL-encoded forms.
