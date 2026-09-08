# Give an Agent a new capability

An extension packages something your team can reuse: instructions, a tool, an app connection,
an evaluator, or a model profile. Start with the smallest piece that solves your problem.

## Choose a package type

| Type | Use it for | Main file |
|---|---|---|
| `skill` | Instructions for a repeatable task | `SKILL.md` |
| `tool` | A named operation with an input schema | `tool.json` |
| `connector` | An application connection and its permitted events | `connector.json` |
| `evaluator` | A way to assess a result | `evaluator.json` |
| `model-profile` | A model's processing route and capabilities | `model-profile.json` |
| `agent-bundle` | A selection of components for an Agent | `agent-bundle-selection.json` |

## Create a tool package

```console
geyser init tool careful-search
geyser validate careful-search
geyser test careful-search
geyser dev careful-search
```

The generated directory contains:

- `geyser-package.json`: name, kind, version, and requested permissions.
- `tool.json`: description, input schema, effect class, and approval posture.
- `evals/cases.json`: declared success and denial fixtures.
- `README.md`: a place to explain the package to its next developer.

In 0.1.0, `test` checks the fixture declarations and `dev` demonstrates a local admission and
completion. Use your own tool tests to exercise its implementation. For an example that actually
calls a registered local function, follow the [emulator quickstart](quickstart.md#follow-a-complete-run).

## Describe the action clearly

Give the tool a name and description that explain what it does. Define its accepted inputs with a
schema. Declare whether it reads information or changes another system, and request only the
permissions it needs. A package requests access; the workspace decides what it receives.

Write examples for both a useful result and an action the tool should decline. For a result your
application needs to parse, add a [structured outcome](outcomes.md).

## Package and connect

```console
geyser package careful-search
```

This creates a local archive and reports its digest. Signing and remote staging come next; see the
[CLI reference](cli.md#publish-an-extension) and [authentication](authentication.md) for the required
project access. For a collection of capabilities, use an [Agent Bundle](bundles.md).
