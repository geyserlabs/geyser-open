# OpenAPI and JSON schemas

The public OpenAPI is exported from the actual FastAPI routes in the owning Cell implementation. The committed snapshot is `openapi/geyser-v1.openapi.json`; SDK model schemas are under `schemas/2026-08-24/`. A shared check prevents the public repository snapshot from drifting from the server export.

The live `/api/v1/openapi.json` at your issued API URL describes the software actually serving your workspace. The public Global schema endpoint describes that server’s revision; it does not prove that every Cell and Agent has upgraded.

## Principal operations

| Resource | Operations |
|---|---|
| `/api/v1/inputs` | Upload immutable, project-owned JSON input or outcome contract |
| `/api/v1/tasks` | Create/list tasks; exact idempotency key required for creation |
| `/api/v1/tasks/{id}` | Read task and version |
| `/api/v1/tasks/{id}/result` | Read a completed, project-owned result |
| `/api/v1/runs` | List project runs and read events, traces and state |
| `/api/v1/capabilities` | Inspect assigned Agent execution flags and runtime profiles |
| `/api/v1/packages` | Upload/list signed packages; promote and revoke exact versions |
| `/api/v1/customer/...` | Authorized human inspection/decisions; project grants remain project-scoped |
| `/api/v1/oauth/...` | Geyser CLI device and loopback-PKCE authentication |

Success bodies include `api_version`. Public failures use RFC problem details; OAuth failures use OAuth error responses. Mutations use `Idempotency-Key` and/or `If-Match` as shown in the specification. `429` includes `Retry-After`. Cursor pagination can return an empty page with a next cursor after authorization filtering; continue until the cursor is empty.

Regenerate SDK schemas with `python scripts/generate_schemas.py`. The OpenAPI snapshot is copied from `fleet-coordinator/scripts/export-developer-openapi.py`, never re-created as a handwritten approximation of the SDK. The API contract version remains `2026-08-24`; the SDK’s 0.2.0 version identifies the compatibility corrections described in the [changelog](changelog.md).
