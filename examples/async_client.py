"""Read-only async client example. Set the token in your own secret source."""

import asyncio
import os

from geyser_sdk import AsyncGeyserClient


async def main() -> None:
    token = os.environ["GEYSER_DEVELOPER_TOKEN"]
    async with AsyncGeyserClient(os.environ["GEYSER_API_URL"], token) as client:
        async for run in client.iter_runs():
            print(run.id, run.state)


if __name__ == "__main__":
    asyncio.run(main())
