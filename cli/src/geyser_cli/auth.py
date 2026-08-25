"""OAuth device flow for humans and bounded service tokens for CI."""

from __future__ import annotations

import time
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx

from .credentials import CredentialStore, StoredCredential

CLIENT_ID = "geyser-public-cli"


@dataclass(frozen=True, slots=True)
class DeviceAuthorization:
    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str
    expires_in: int
    interval: int


def login_device(
    base_url: str,
    store: CredentialStore,
    *,
    scopes: list[str],
    open_browser: bool = True,
    timeout: float = 10.0,
    notify: Callable[[DeviceAuthorization], None] | None = None,
) -> dict[str, Any]:
    with httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout) as client:
        response = client.post(
            "/api/v1/oauth/device/code",
            json={"client_id": CLIENT_ID, "scope": " ".join(scopes)},
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"device authorization could not start ({response.status_code})"
            )
        device = DeviceAuthorization(**response.json())
        if notify:
            notify(device)
        if open_browser:
            webbrowser.open(device.verification_uri_complete or device.verification_uri)
        deadline = time.monotonic() + device.expires_in
        interval = max(1, device.interval)
        while time.monotonic() < deadline:
            token_response = client.post(
                "/api/v1/oauth/token",
                json={
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": device.device_code,
                    "client_id": CLIENT_ID,
                },
            )
            value = token_response.json()
            if token_response.status_code == 200:
                credential = StoredCredential(
                    access_token=str(value["access_token"]),
                    token_type=str(value.get("token_type") or "Bearer"),
                    expires_at=time.time() + float(value.get("expires_in") or 0),
                    scope=str(value.get("scope") or ""),
                    customer_id=int(value.get("customer_id") or 0),
                    project_id=str(value.get("project_id") or ""),
                )
                backend = store.save(credential)
                return {
                    "authenticated": True,
                    "storage": backend,
                    "scope": credential.scope.split(),
                    "customer_id": credential.customer_id,
                    "project_id": credential.project_id,
                }
            error = str(value.get("error") or "")
            if error == "authorization_pending":
                time.sleep(interval)
                continue
            if error == "slow_down":
                interval += 5
                time.sleep(interval)
                continue
            failure = error or str(token_response.status_code)
            raise RuntimeError(f"device authorization failed: {failure}")
    raise RuntimeError("device authorization expired")


def login_service_token(store: CredentialStore, token: str) -> dict[str, Any]:
    if not token.strip():
        raise ValueError("service token input was empty")
    backend = store.save(StoredCredential(access_token=token.strip()))
    return {"authenticated": True, "storage": backend, "credential_type": "service"}


__all__ = ["CLIENT_ID", "DeviceAuthorization", "login_device", "login_service_token"]
