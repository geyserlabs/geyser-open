# Five-minute emulator quickstart

Requires Python 3.11–3.13. The local path uses no network and no credential.

```console
python -m venv .venv
. .venv/bin/activate
python -m pip install geyser-sdk geyser-open
geyser init tool careful-search
geyser validate careful-search
geyser test careful-search
geyser dev careful-search
```

Run `python examples/emulator_quickstart.py` from the source repository to observe admission,
durable event ordering, an exact-bound approval, a consequential tool receipt, a checkpoint, and
completion. A successful local test is not runtime qualification or production authority.
