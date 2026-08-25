from __future__ import annotations

import json
import stat
import zipfile
from pathlib import Path

import pytest
from geyser_cli.__main__ import main
from geyser_cli.credentials import CredentialStore, StoredCredential
from geyser_cli.extensions import inspect_archive, package_extension


def test_complete_local_workflow(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--json", "init", "tool", "careful-search", "--output", str(tmp_path)]) == 0
    root = tmp_path / "careful-search"
    created = json.loads(capsys.readouterr().out)
    assert created["created"] is True
    assert main(["--json", "validate", str(root)]) == 0
    assert json.loads(capsys.readouterr().out)["valid"] is True
    assert main(["--json", "test", str(root)]) == 0
    assert json.loads(capsys.readouterr().out)["passed"] == 2
    assert main(["--json", "dev", str(root)]) == 0
    assert json.loads(capsys.readouterr().out)["network_used"] is False
    assert main(["--json", "package", str(root)]) == 0
    packaged = json.loads(capsys.readouterr().out)
    archive = Path(packaged["path"])
    first = archive.read_bytes()
    assert package_extension(root)["digest"] == packaged["digest"]
    assert archive.read_bytes() == first
    assert inspect_archive(archive)["files"] >= 4


def test_outcome_cli_and_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    contract = tmp_path / "contract.json"
    result = tmp_path / "result.json"
    contract.write_text(json.dumps({
        "schema_version": 1,
        "schema_ref": "example:answer:v1",
        "json_schema": {
            "type": "object", "properties": {"answer": {"type": "string"}},
            "required": ["answer"], "additionalProperties": False,
        },
    }))
    result.write_text('{"answer":"yes"}')
    assert main(["--json", "validate-outcome", str(contract), str(result)]) == 0
    assert json.loads(capsys.readouterr().out)["valid"] is True
    result.write_text('{"wrong":true}')
    assert main(["--json", "validate-outcome", str(contract), str(result)]) == 2
    assert "OutcomeValidationError" in capsys.readouterr().out
    assert main(["--json", "init", "tool", "BAD", "--output", str(tmp_path)]) == 2


def test_archive_traversal_symlink_and_bounds(tmp_path: Path) -> None:
    traversal = tmp_path / "traversal.zip"
    with zipfile.ZipFile(traversal, "w") as archive:
        archive.writestr("../escape", "bad")
    with pytest.raises(ValueError, match="traversal"):
        inspect_archive(traversal)
    symlink = tmp_path / "symlink.zip"
    with zipfile.ZipFile(symlink, "w") as archive:
        info = zipfile.ZipInfo("link")
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(info, "target")
    with pytest.raises(ValueError, match="symbolic link"):
        inspect_archive(symlink)


def test_explicit_restricted_file_credential_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unavailable(*_args: object) -> None:
        raise RuntimeError("no keychain")

    monkeypatch.setattr("geyser_cli.credentials.keyring.set_password", unavailable)
    monkeypatch.setattr("geyser_cli.credentials.keyring.get_password", unavailable)
    monkeypatch.setattr("geyser_cli.credentials.keyring.delete_password", unavailable)
    denied = CredentialStore("test", allow_file_fallback=False)
    denied.path = tmp_path / "credentials.json"
    with pytest.raises(RuntimeError, match="opt in"):
        denied.save(StoredCredential(access_token="secret"))  # noqa: S106 - test fixture
    store = CredentialStore("test", allow_file_fallback=True)
    store.path = tmp_path / "credentials.json"
    assert store.save(StoredCredential(access_token="secret")) == "restricted-file"  # noqa: S106
    assert stat.S_IMODE(store.path.stat().st_mode) == 0o600
    assert store.load() is not None
    assert store.load().access_token == "secret"  # type: ignore[union-attr]  # noqa: S105
    assert store.delete() is True
    assert not store.path.exists()


def test_version_is_machine_readable(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--json", "version"]) == 0
    assert json.loads(capsys.readouterr().out)["geyser_open"] == "0.1.0b4"
