# Agent Bundle configuration preview

The public CLI can scaffold, validate and package an `agent-bundle` selection. This is a configuration preview, not an installed Agent runtime.

```console
geyser init agent-bundle careful-assistant
geyser validate careful-assistant
geyser package careful-assistant
```

The JSON extension consumer does not activate these bundles. `geyser test` and `geyser dev` require an executable `tool`, `connector`, or `evaluator` handler. Public OpenClaw/Letta import, credential migration, runtime installation and bundle rollout are not implemented features of this CLI. Archive inspection alone is not an importer or an execution guarantee.

Use the supported [JSON extension contract](extensions.md) for executable public packages. Workspace runtime and Agent configuration remain first-party controls.
