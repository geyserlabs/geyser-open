from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import urllib.error
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "recover_release", Path(__file__).parents[1] / "scripts/recover_release.py",
)
assert SPEC and SPEC.loader
recovery = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(recovery)


@pytest.mark.parametrize("wrong_source", [False, True])
def test_recovery_requires_exact_tag_build(monkeypatch, wrong_source):
    monkeypatch.setenv("RELEASE_TAG", "v0.2.0")
    monkeypatch.setenv("GITHUB_REF", "refs/tags/v0.2.0-publish-20260909")
    monkeypatch.setenv("REUSE_RUN_ID", "123")
    monkeypatch.setattr(recovery.subprocess, "check_output", lambda *a, **kw: "a" * 40)
    jobs = ["python-distributions", "assemble",
            "standalone-cli (macos-14, darwin-arm64)",
            "standalone-cli (ubuntu-24.04, linux-amd64)"]
    values = {
        "actions/runs/123": {
            "head_sha": ("b" if wrong_source else "a") * 40,
            "workflow_id": 456, "repository": {"full_name": recovery.REPO},
            "event": "push",
        },
        "actions/workflows/release.yml": {"id": 456},
        "actions/runs/123/jobs?per_page=100": {
            "jobs": [{"name": name, "conclusion": "success"} for name in jobs],
        },
    }
    monkeypatch.setattr(recovery, "api", lambda path: values[path])
    if wrong_source:
        with pytest.raises(ValueError, match="exact release source"):
            recovery.verify_source()
    else:
        recovery.verify_source()


@pytest.mark.parametrize("tag", ["main", "v0.2.0/../main", "v0.2.0;date"])
def test_recovery_rejects_non_version_tags(monkeypatch, tag):
    monkeypatch.setenv("RELEASE_TAG", tag)
    with pytest.raises(ValueError, match="exact version"):
        recovery.release_version()


@pytest.mark.parametrize("ref", [
    "refs/heads/main", "refs/pull/44/merge", "refs/tags/v0.3.0-publish-20260909",
])
def test_recovery_rejects_unrelated_workflow_refs(monkeypatch, ref):
    monkeypatch.setenv("RELEASE_TAG", "v0.2.0")
    monkeypatch.setenv("GITHUB_REF", ref)
    with pytest.raises(ValueError, match="immutable publication tag"):
        recovery.verify_source()


@pytest.mark.parametrize("status", [404, 403, 503, "same", "different"])
def test_publication_retry_requires_missing_version_or_exact_existing_hashes(
    monkeypatch, tmp_path, status,
):
    files = ["geyser_sdk-0.2.0.tar.gz", "geyser_sdk-0.2.0-py3-none-any.whl"]
    for name in files:
        (tmp_path / name).write_bytes(b"verified-artifact")
    def response(*args, **kwargs):
        if isinstance(status, int):
            raise urllib.error.HTTPError("https://pypi.org/", status, "test", {}, None)
        digest = hashlib.sha256(b"verified-artifact").hexdigest()
        return io.BytesIO(json.dumps({
            "info": {"name": "geyser-sdk", "version": "0.2.0"},
            "urls": [{"filename": name, "digests": {
                "sha256": digest if status == "same" else "0" * 64,
            }} for name in files],
        }).encode())
    monkeypatch.setattr(recovery.urllib.request, "urlopen", response)
    if status == 404:
        assert recovery.already_published(tmp_path, "geyser-sdk", "0.2.0") is False
    elif status == "same":
        assert recovery.already_published(tmp_path, "geyser-sdk", "0.2.0") is True
    else:
        with pytest.raises((ValueError, urllib.error.HTTPError)):
            recovery.already_published(tmp_path, "geyser-sdk", "0.2.0")
