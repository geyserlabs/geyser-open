"""Read-only sync client example. Set the token in your own secret source."""

from geyser_sdk import GeyserClient

token = "replace-with-bounded-developer-token"  # noqa: S105 - inert documentation value
with GeyserClient("https://agents.geyserlabs.ai", token) as client:
    for run in client.iter_runs():
        print(run.id, run.state)
