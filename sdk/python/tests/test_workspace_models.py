from __future__ import annotations

from typing import Any

import httpx
import pytest
from geyser_sdk import (
    MODELS_INFER_SCOPE,
    AsyncGeyserClient,
    GeyserClient,
    ProblemError,
    ResponseValidationError,
    WorkspaceModelList,
    anthropic_base_url,
    openai_base_url,
)


def model_list() -> dict[str, Any]:
    return {
        "object": "list",
        "data": [
            {
                "id": "private/pmd_support_v2",
                "object": "model",
                "created": 1790000000,
                "owned_by": "geyser",
                "geyser": {
                    "display_name": "Support replies",
                    "state": "running",
                    "context_window": 32768,
                    "future_field": True,
                },
            },
            {
                "id": "private/pmd_triage_v1",
                "object": "model",
                "created": 1790000100,
                "owned_by": "geyser",
                "geyser": {"display_name": "Triage", "state": "warming", "context_window": 8192},
            },
        ],
    }


def test_list_models_uses_openai_compatible_route_and_bearer() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=model_list())

    with GeyserClient(
        "https://cell.example/", "gdp_service", transport=httpx.MockTransport(handler)
    ) as client:
        listed = client.list_models()
    assert isinstance(listed, WorkspaceModelList)
    assert [model.id for model in listed.data] == [
        "private/pmd_support_v2",
        "private/pmd_triage_v1",
    ]
    assert listed.data[0].geyser.display_name == "Support replies"
    assert listed.data[0].geyser.context_window == 32768
    # Unknown states and fields survive for forward compatibility.
    assert listed.data[1].geyser.state == "warming"
    assert listed.data[0].geyser.model_dump()["future_field"] is True
    assert requests[0].method == "GET"
    assert requests[0].url.path == "/api/v1/openai/models"
    assert requests[0].headers["Authorization"] == "Bearer gdp_service"
    assert MODELS_INFER_SCOPE == "models:infer"


async def test_async_list_models_and_base_urls() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"object": "list", "data": []})

    async with AsyncGeyserClient(
        "https://cell.example/c/607I/", "token", transport=httpx.MockTransport(handler)
    ) as client:
        assert (await client.list_models()).data == []
        assert client.openai_base_url() == "https://cell.example/c/607I/api/v1/openai"
        assert client.anthropic_base_url() == "https://cell.example/c/607I/api/v1/anthropic"


def test_base_url_helpers_follow_the_issued_api_url() -> None:
    with GeyserClient("http://localhost:8000", "token") as client:
        assert client.openai_base_url() == "http://localhost:8000/api/v1/openai"
        assert client.anthropic_base_url() == "http://localhost:8000/api/v1/anthropic"
    assert openai_base_url("https://cell.example/") == "https://cell.example/api/v1/openai"
    assert anthropic_base_url("https://cell.example") == "https://cell.example/api/v1/anthropic"
    with pytest.raises(ValueError, match="HTTPS"):
        openai_base_url("http://cell.example")
    with pytest.raises(ValueError):
        anthropic_base_url("https://cell.example/?token=secret")


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (401, "invalid_api_key"),
        (403, "insufficient_scope"),
        (403, "developer_inference_disabled"),
        (404, "model_not_found"),
        (409, "model_changed"),
    ],
)
def test_openai_error_shape_becomes_problem(status: int, code: str) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status,
            json={"error": {"message": "Plain explanation.", "type": "geyser_error", "code": code}},
        )

    with GeyserClient(
        "https://cell.example", "token", transport=httpx.MockTransport(handler)
    ) as client, pytest.raises(ProblemError) as caught:
        client.list_models()
    assert caught.value.problem.status == status
    assert caught.value.problem.code == code
    assert caught.value.problem.detail == "Plain explanation."
    assert caught.value.problem.title == "geyser_error"


def test_rate_limited_list_honors_retry_after(monkeypatch: pytest.MonkeyPatch) -> None:
    delays: list[float] = []
    monkeypatch.setattr("geyser_sdk.client.time.sleep", delays.append)
    responses = iter(
        [
            httpx.Response(
                429,
                headers={"Retry-After": "3"},
                json={
                    "error": {"message": "Slow down.", "type": "rate_limit", "code": "rate_limited"}
                },
            ),
            httpx.Response(200, json=model_list()),
        ]
    )

    with GeyserClient(
        "https://cell.example", "token", transport=httpx.MockTransport(lambda _r: next(responses))
    ) as client:
        assert len(client.list_models().data) == 2
    assert delays == [3.0]


def test_anthropic_error_shape_and_invalid_list() -> None:
    def anthropic_error(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            503,
            json={
                "type": "error",
                "error": {"type": "model_unavailable", "message": "The computer is asleep."},
            },
        )

    with GeyserClient(
        "https://cell.example",
        "token",
        max_retries=0,
        transport=httpx.MockTransport(anthropic_error),
    ) as client, pytest.raises(ProblemError) as caught:
        client.list_models()
    assert caught.value.problem.code == "model_unavailable"
    assert caught.value.problem.status == 503

    with GeyserClient(
        "https://cell.example",
        "token",
        transport=httpx.MockTransport(lambda _r: httpx.Response(200, json={"object": "list"})),
    ) as client, pytest.raises(ResponseValidationError):
        client.list_models()
