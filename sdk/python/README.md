# geyser-sdk

Typed sync/async clients and a deterministic, credential-free local emulator
for Geyser's public `/api/v1` developer contract.

```python
from geyser_sdk import GeyserClient

with GeyserClient("https://api.geyserlabs.ai", access_token="...") as geyser:
    for run in geyser.runs.iter():
        print(run.id, run.state)
```

Tokens are always explicit. The package never reads an ambient Agent key,
provider credential, or browser session.
