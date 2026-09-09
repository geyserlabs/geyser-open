from __future__ import annotations

from typing import Any

import httpx
import pytest
from geyser_sdk import AsyncGeyserClient, EmulatorError, GeyserClient, LocalEmulator, TypedTask
from geyser_sdk.client import _retry_delay
from geyser_sdk.urls import require_credential_destination, validate_api_url
from test_client import SHA, run_value


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost.attacker.invalid",
        "http://127.0.0.1.attacker.invalid",
        "https://user:password@example.com",
        "http://example.com",
        "https://example.com?token=x",
        "https://example.com/#x",
        "https://example.com\\@localhost",
        "https://example.com:bad",
        "https://example.com:0",
        "https://exam\nple.com",
    ],
)
def test_credential_destination_rejected_before_transport(url: str) -> None:
    for client in (GeyserClient, AsyncGeyserClient):
        with pytest.raises(ValueError):
            client(url, "synthetic-token")


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:8234",
        "http://127.0.0.1",
        "http://[::1]:8234",
        "https://api.example/cell/one",
    ],
)
def test_exact_loopback_and_https(url: str) -> None:
    assert validate_api_url(url) == url
    assert require_credential_destination(url, url) == url
    with pytest.raises(ValueError):
        require_credential_destination(url, "https://another.example")


def terminal_race() -> Any:
    pages = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal pages
        if request.url.path.endswith("/events"):
            pages += 1
            sequence = 1 if pages == 1 else 2
            event = {
                "sequence": sequence,
                "event_type": "run.started" if sequence == 1 else "run.completed",
                "event_id": f"event-{sequence}",
                "observed_at": 1,
                "created_at": 1,
                "data": {},
                "digest": SHA,
            }
            return httpx.Response(200, json={"data": [event], "current_sequence": sequence})
        return httpx.Response(200, json={"run": run_value()})

    return handler


def test_sync_watch_drains_terminal_event(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("geyser_sdk.client.time.sleep", lambda _: None)
    with GeyserClient(
        "https://api.example", "test", transport=httpx.MockTransport(terminal_race())
    ) as client:
        assert [event.sequence for event in client.watch_events("run-1")] == [1, 2]


@pytest.mark.asyncio
async def test_async_watch_drains_terminal_event(monkeypatch: pytest.MonkeyPatch) -> None:
    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr("geyser_sdk.client.asyncio.sleep", no_sleep)
    async with AsyncGeyserClient(
        "https://api.example", "test", transport=httpx.MockTransport(terminal_race())
    ) as client:
        assert [event.sequence async for event in client.watch_events("run-1")] == [1, 2]


def test_retry_after_respected() -> None:
    assert _retry_delay(httpx.Response(429, headers={"Retry-After": "17"}), 0) == 17
    assert _retry_delay(httpx.Response(429, headers={"Retry-After": "invalid"}), 0) == 0.1


@pytest.mark.asyncio
async def test_unknown_effect_requires_reconciliation() -> None:
    emulator = LocalEmulator()
    emulator.admit("run-test", TypedTask(task_id="test", context_id="test", prompt_digest=SHA))
    calls = 0

    def consequential(arguments: Any) -> Any:
        nonlocal calls
        calls += 1
        raise RuntimeError("connection lost after effect")

    emulator.register_tool("send", consequential)
    with pytest.raises(RuntimeError):
        await emulator.call_tool("run-test", tool_name="send", arguments={"id": "once"})
    with pytest.raises(EmulatorError, match="unknown"):
        await emulator.call_tool("run-test", tool_name="send", arguments={"id": "once"})
    effect = emulator.events["run-test"][-1]["data"]["effect_id"]
    emulator.reconcile_tool("run-test", effect_id=effect, result={"sent": True})
    assert await emulator.call_tool("run-test", tool_name="send", arguments={"id": "once"}) == {
        "sent": True
    }
    assert calls == 1


@pytest.mark.asyncio
async def test_operation_identity_binds_retries_and_new_intent() -> None:
    emulator = LocalEmulator()
    emulator.admit("run-test", TypedTask(task_id="test", context_id="test", prompt_digest=SHA))
    calls = []

    async def write(arguments: Any) -> Any:
        calls.append(arguments)
        return {"written": len(calls)}

    emulator.register_tool("write", write)
    first = await emulator.call_tool(
        "run-test", tool_name="write", arguments={"value": 1}, operation_id="change-1"
    )
    assert (
        await emulator.call_tool(
            "run-test", tool_name="write", arguments={"value": 1}, operation_id="change-1"
        )
        == first
    )
    with pytest.raises(EmulatorError, match="different invocation"):
        await emulator.call_tool(
            "run-test", tool_name="write", arguments={"value": 2}, operation_id="change-1"
        )
    assert await emulator.call_tool(
        "run-test", tool_name="write", arguments={"value": 1}, operation_id="change-2"
    ) == {"written": 2}
    with pytest.raises(EmulatorError, match="operation_id"):
        await emulator.call_tool(
            "run-test", tool_name="write", arguments={}, operation_id="bad\nidentity"
        )
    assert len(calls) == 2


@pytest.mark.parametrize(
    "budget",
    [
        {"max_cost_usd": -1},
        {"max_cost_usd": True},
        {"max_elapsed_seconds": float("inf")},
        {"max_provider_requests": 1.5},
        {"max_tool_calls": 0},
        {"invented": 1},
        {"max_cost_usd": 10**1000},
        {"max_cost_usd": "1"},
    ],
)
def test_invalid_budget_rejected_before_transport(budget: dict[str, Any]) -> None:
    from geyser_sdk.models import TaskCreate

    with pytest.raises(ValueError):
        TaskCreate(input_ref="gdev:dobj_" + "a" * 64, input_digest=SHA, budget=budget)
