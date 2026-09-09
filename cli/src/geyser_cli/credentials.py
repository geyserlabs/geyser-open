"""Credential storage with keychain-first, explicitly opted-in file fallback."""

from __future__ import annotations

import json
import os
import stat
from dataclasses import asdict, dataclass
from tempfile import NamedTemporaryFile

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
    api_url: str = ""
    cell_generation: int = 0


class CredentialStore:
    def __init__(self, profile: str = "default", *, allow_file_fallback: bool = False) -> None:
        self.profile = profile
        self.allow_file_fallback = allow_file_fallback
        self.path = user_config_path("geyser", "Geyser Labs") / "credentials.json"

    def save(self, credential: StoredCredential) -> str:
        payload = json.dumps(asdict(credential))
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
            existing = self._read_file()
        existing[self.profile] = payload
        self._write_file(existing)
        return "restricted-file"

    def _read_file(self) -> dict[str, str]:
        descriptor = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, "r", encoding="utf-8") as stream:
            info = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(info.st_mode)
                or stat.S_IMODE(info.st_mode) != 0o600
                or info.st_uid != os.getuid()
            ):
                raise RuntimeError(
                    "credential fallback must be a regular 0600 file owned by this user"
                )
            payload = stream.read(1024 * 1024 + 1)
            if len(payload) > 1024 * 1024:
                raise RuntimeError("credential fallback exceeds 1 MiB")
        values: dict[str, str] = json.loads(payload)
        return values

    def _write_file(self, values: dict[str, str]) -> None:
        # mkstemp creates 0600 atomically; no interval with a world-readable token.
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=self.path.parent, prefix=".credentials-", delete=False
        ) as stream:
            temporary = stream.name
            try:
                json.dump(values, stream)
                stream.flush()
                os.fsync(stream.fileno())
                os.replace(temporary, self.path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)

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
            payload = self._read_file().get(self.profile)
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
            values = self._read_file()
            removed = values.pop(self.profile, None) is not None or removed
            if values:
                self._write_file(values)
            else:
                self.path.unlink()
        return removed


__all__ = ["CredentialStore", "StoredCredential"]
