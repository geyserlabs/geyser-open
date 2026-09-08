# Versions and compatibility

## Supported surfaces

| Surface | Current version | Supported use |
|---|---|---|
| Python SDK | 0.1.0 | Python 3.11–3.13; synchronous and asynchronous clients |
| Python CLI | 0.1.0 | Python 3.11–3.13 |
| Standalone CLI | 0.1.0 | Apple silicon macOS and Ubuntu 24.04 AMD64 |
| Homebrew CLI | 0.1.0 | `geyserlabs/tap/geyser` |
| Developer API | v1, contract `2026-08-24` | Authenticated task, run, package, approval, and capability operations |
| Local emulator | Included in SDK 0.1.0 | Credential-free development and deterministic examples |

The Python packages are platform-independent. Windows does not yet have a declared standalone
CLI build. Install from the [public release channels](releases.md).

## API compatibility

API v1 is additive. The current and previous SDK minor versions are supported against the current
server. Deprecations are documented for at least one minor version before removal, except when a
security issue needs an immediate change.

Use [typed SDK clients](sdk.md) for request and response handling. Read the
[live OpenAPI document](https://agents.geyserlabs.ai/api/v1/openapi.json) for the current API shape.

## Runtime capabilities

A runtime's capabilities depend on its framework, backend, adapter version, model profile,
placement, and privacy settings. Check the Agent you intend to use:

```console
geyser capabilities --agent YOUR_AGENT_NAME
```

Capability values mean:

| Value | Meaning |
|---|---|
| `native` | The selected runtime implements the capability directly |
| `geyser_emulated` | Geyser supplies the capability around the selected runtime |
| `unsupported` | This configuration does not implement it |
| `forbidden` | Policy disallows it in this configuration |

The response for your Agent is the useful source for a runtime decision. A successful local
emulator run does not change that Agent's permissions or supported capabilities.

## Earlier releases

The 0.1.0 beta releases are superseded by 0.1.0. See the [changelog](changelog.md) for the features
introduced in each published release.
