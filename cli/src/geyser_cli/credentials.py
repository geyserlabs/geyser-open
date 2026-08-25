"""Credential storage with keychain-first, explicitly opted-in file fallback."""

from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass

import keyring
from keyring.errors import KeyringError
from platformdirs import user_config_path

SERVICE = "ai.geyser.developer-cli"


@dataclass(frozen=True, slots=True)
class StoredCredential:
    access_token: str
    token_type: str = "Bearer"  # noqa: S105 - OAuth token scheme, not a secret
    expires_at: float = 0
    scope: str = ""
    customer_id: int = 0
    project_id: str = ""


class CredentialStore:
    def __init__(self, profile: str = "default", *, allow_file_fallback: bool = False) -> None:
        self.profile = profile
        self.allow_file_fallback = allow_file_fallback
        self.path = user_config_path("geyser", "Geyser Labs") / "credentials.json"

    def save(self, credential: StoredCredential) -> str:
        payload = json.dumps(credential.__dict__ if hasattr(credential, "__dict__") else {
            "access_token": credential.access_token,
            "token_type": credential.token_type,
            "expires_at": credential.expires_at,
            "scope": credential.scope,
            "customer_id": credential.customer_id,
            "project_id": credential.project_id,
        })
        try:
            keyring.set_password(SERVICE, self.profile, payload)
            return "os-keychain"
        except (KeyringError, RuntimeError):
            if not self.allow_file_fallback:
                raise RuntimeError(
                    "OS keychain is unavailable; rerun with --allow-file-credentials to opt in "
                    "to a permission-restricted file"
                ) from None
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        existing: dict[str, str] = {}
        if self.path.exists():
            existing = json.loads(self.path.read_text(encoding="utf-8"))
        existing[self.profile] = payload
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(existing), encoding="utf-8")
        os.chmod(temporary, stat.S_IRUSR | stat.S_IWUSR)
        temporary.replace(self.path)
        return "restricted-file"

    def load(self) -> StoredCredential | None:
        payload: str | None = None
        try:
            payload = keyring.get_password(SERVICE, self.profile)
        except (KeyringError, RuntimeError):
            pass
        if payload is None and self.allow_file_fallback and self.path.exists():
            mode = stat.S_IMODE(self.path.stat().st_mode)
            if mode & 0o077:
                raise RuntimeError("credential fallback file permissions are not 0600")
            payload = json.loads(self.path.read_text(encoding="utf-8")).get(self.profile)
        if payload is None:
            return None
        value = json.loads(payload)
        return StoredCredential(**value)

    def delete(self) -> bool:
        removed = False
        try:
            if keyring.get_password(SERVICE, self.profile) is not None:
                keyring.delete_password(SERVICE, self.profile)
                removed = True
        except (KeyringError, RuntimeError):
            pass
        if self.allow_file_fallback and self.path.exists():
            values = json.loads(self.path.read_text(encoding="utf-8"))
            removed = values.pop(self.profile, None) is not None or removed
            if values:
                self.path.write_text(json.dumps(values), encoding="utf-8")
                os.chmod(self.path, 0o600)
            else:
                self.path.unlink()
        return removed


__all__ = ["CredentialStore", "StoredCredential"]
