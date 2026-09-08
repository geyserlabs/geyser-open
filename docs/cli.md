# CLI reference

Use `geyser --help` for top-level options and `geyser COMMAND --help` for a command's arguments.
Global flags go **before** the command:

```console
geyser --json version
geyser --json doctor
geyser --profile work runs list
```

## Work locally

| Command | What it does |
|---|---|
| `geyser init tool NAME` | Create a tool scaffold |
| `geyser validate PATH` | Check a package's declarations |
| `geyser test PATH` | Check its success and denial fixtures |
| `geyser dev PATH` | Demonstrate a local emulator run |
| `geyser validate-outcome SCHEMA RESULT` | Check a JSON result against its schema |
| `geyser package PATH` | Create a local package archive |

`init` also accepts `skill`, `connector`, `evaluator`, `model-profile`, and `agent-bundle`.
Start with the [quickstart](quickstart.md) for a complete example.

## Connect and inspect

| Command | What it does |
|---|---|
| `geyser login` | Sign in through OAuth device authorization |
| `geyser logout` | Remove the current profile's saved credential |
| `geyser doctor` | Check configuration and API reachability |
| `geyser runs list` | List accessible runs |
| `geyser runs get RUN_ID` | Read a run's current state |
| `geyser runs watch RUN_ID` | Follow its events |
| `geyser runs trace RUN_ID` | Export its recorded trace |
| `geyser approvals list` | List approvals |
| `geyser approvals get APPROVAL_ID` | Read an approval's exact binding |
| `geyser capabilities --agent NAME` | Inspect an Agent's available capabilities |

## Make a decision or change a run

`runs stop`, `runs fork`, and `approvals decide` require the current sequence. Approval decisions
also require the binding digest and a reason. Use `--help` to see the required fields and read the
current run or approval immediately before acting.

Mutating commands show the intended action and request confirmation. `--yes` accepts that local
preview; the server still checks your scope, the current state, and the applicable policy.

## Publish an extension

Package creation, signing, upload, staging, and promotion are separate steps. `sign` signs the
archive. `publish ARCHIVE --stage` uploads signed bytes for staging. `promote PACKAGE_ID --digest
DIGEST --canary` requests a canary promotion. `status` lists package lifecycle state.

Each remote step needs the corresponding project scope. Read [authentication](authentication.md)
and [Agent Bundles](bundles.md) before publishing.
