"""Read-only sync client example. Set the token in your own secret source."""

import os

from geyser_sdk import GeyserClient

token = os.environ["GEYSER_DEVELOPER_TOKEN"]
with GeyserClient(os.environ["GEYSER_API_URL"], token) as client:
    for run in client.iter_runs():
        print(run.id, run.state)
