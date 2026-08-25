from __future__ import annotations

from typing import Any

import httpx
import pytest
from geyser_cli.auth import login_device
from geyser_cli.credentials import StoredCredential


class MemoryStore:
    credential: StoredCredential | None = None

    def save(self, credential: StoredCredential) -> str:
        self.credential = credential
        return "test-keychain"


def test_device_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = iter([
        httpx.Response(200, json={
            "device_code": "device-secret",
            "user_code": "ABCD-EFGH",
            "verification_uri": "https://auth.example/device",
            "verification_uri_complete": "https://auth.example/device?code=ABCD-EFGH",
            "expires_in": 60,
            "interval": 1,
        }),
        httpx.Response(400, json={"error": "authorization_pending"}),
        httpx.Response(200, json={
            "access_token": "access-secret",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "development:read runs:read",
            "customer_id": 1,
            "project_id": "project-1",
        }),
    ])

    class Client:
        def __init__(self, **_kwargs: Any) -> None:
            pass

        def __enter__(self) -> Client:
            return self

        def __exit__(self, *_args: object) -> None:
            pass

        def post(self, *_args: object, **_kwargs: object) -> httpx.Response:
            return next(responses)

    monkeypatch.setattr("geyser_cli.auth.httpx.Client", Client)
    monkeypatch.setattr("geyser_cli.auth.time.sleep", lambda _seconds: None)
    store = MemoryStore()
    notifications: list[str] = []
    value = login_device(
        "https://api.example",
        store,  # type: ignore[arg-type]
        scopes=["development:read"],
        open_browser=False,
        notify=lambda device: notifications.append(device.user_code),
    )
    assert value["storage"] == "test-keychain"
    assert store.credential is not None
    assert store.credential.access_token == "access-secret"  # noqa: S105 - test fixture
    assert notifications == ["ABCD-EFGH"]
