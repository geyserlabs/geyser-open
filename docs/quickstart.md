# Build your first tool

In a few minutes, you'll create a tool package, validate it, and exercise it locally. No account
or credentials are needed. Installing the packages uses the network; the emulator itself runs locally.

## Install the tools

Use Python 3.11–3.13. These commands create a separate environment for the example:

```console
python -m venv .venv
. .venv/bin/activate
python -m pip install geyser-sdk==0.1.0 geyser-open==0.1.0
geyser --json version
```

On Windows, activate the environment with `.venv\Scripts\Activate.ps1` in PowerShell.

## Create and check a tool

```console
geyser init tool careful-search
geyser validate careful-search
geyser test careful-search
geyser dev careful-search
```

`init` creates the package files. `validate` checks their declarations. `test` checks the package's
success and denial fixture declarations. `dev` demonstrates admission and completion in the local emulator.

Open the new `careful-search` directory. The manifest describes the tool and its requested
permissions; the fixtures describe the behavior its tests expect. Change the package, then run
`validate` and `test` again. See [extensions](extensions.md) for the other package types.

## Follow a complete run

The source repository includes an example with a local tool, a specific approval, a checkpoint,
and completion. Clone the released version and run it with the environment you just installed:

```console
git clone --depth 1 --branch v0.1.0 https://github.com/geyserlabs/geyser-open.git
cd geyser-open
python examples/emulator_quickstart.py
```

The example stores the value `42` through a deterministic local function. Its final JSON projection
shows the run state and event sequence. No model or external application is called.

[Read the complete example](https://github.com/geyserlabs/geyser-open/blob/v0.1.0/examples/emulator_quickstart.py)
to see how the task, approval, tool call, and checkpoint fit together.

## Connect to your workspace

When you have a Geyser account and project access, [sign in](authentication.md) and inspect the
runs you can access:

```console
geyser login
geyser runs list
```

Local testing gives you a working package to develop. Your workspace's permissions and configured
runtime determine what it can do remotely. Next, [use the SDK](sdk.md) or try a
[practical recipe](recipes.md).
