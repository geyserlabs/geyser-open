"""Read-only async client example. Set the token in your own secret source."""

import asyncio

from geyser_sdk import AsyncGeyserClient


async def main() -> None:
    token = "replace-with-bounded-developer-token"  # noqa: S105 - inert documentation value
    async with AsyncGeyserClient("https://agents.geyserlabs.ai", token) as client:
        async for run in client.iter_runs():
            print(run.id, run.state)


if __name__ == "__main__":
    asyncio.run(main())
