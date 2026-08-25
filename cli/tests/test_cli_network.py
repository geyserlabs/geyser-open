from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from geyser_cli import __main__ as cli
from geyser_cli.extensions import package_extension
from geyser_cli.scaffolds import scaffold

SHA = "sha256:" + "a" * 64


class FakeClient:
    def __enter__(self) -> FakeClient:
        return self

    def __exit__(self, *_args: object) -> None:
        pass

    def list_packages(self) -> dict[str, Any]:
        return {"data": []}

    def capabilities(self, *, agent_name: str) -> dict[str, Any]:
        return {"agent_name": agent_name, "capabilities": {}}

    def list_runs(self, *, customer: bool = False) -> dict[str, Any]:
        return {"data": [], "customer": customer}

    def get_run(self, run_id: str, *, customer: bool = False) -> dict[str, Any]:
        return {"run_id": run_id, "customer": customer}

    def trace(self, run_id: str, *, customer: bool = False) -> dict[str, Any]:
        return {"trace_id": run_id, "customer": customer}

    def watch_events(self, run_id: str, *, customer: bool = False) -> Iterator[dict[str, Any]]:
        yield {"run_id": run_id, "customer": customer}

    def cancel_run(self, run_id: str, request: Any) -> dict[str, Any]:
        return {"run_id": run_id, "cancellation_id": request.cancellation_id}

    def fork(self, run_id: str, request: Any) -> dict[str, Any]:
        return {"run_id": run_id, "fork_id": request.fork_id}

    def list_approvals(self) -> dict[str, Any]:
        return {"data": []}

    def get_approval(self, approval_id: str) -> dict[str, Any]:
        return {"approval_id": approval_id}

    def decide_approval(self, run_id: str, approval_id: str, decision: Any) -> dict[str, Any]:
        return {"run_id": run_id, "approval_id": approval_id, "decision": decision.decision}

    def upload_package(self, package: Any, *, idempotency_key: str) -> dict[str, Any]:
        return {"name": package.name, "digest": idempotency_key, "stage": "staging"}

    def promote_package(self, package_id: str, promotion: Any) -> dict[str, Any]:
        return {"package_id": package_id, "target": promotion.target}


@pytest.mark.parametrize("arguments", [
    ["status"],
    ["capabilities", "--agent", "Ada"],
    ["runs", "list", "--customer"],
    ["runs", "get", "run-1"],
    ["runs", "watch", "run-1"],
    ["runs", "trace", "run-1", "--customer"],
    ["runs", "stop", "run-1", "--expected-sequence", "2", "--yes"],
    ["runs", "fork", "run-1", "--child-run-id", "run-2", "--expected-sequence", "2", "--yes"],
    ["approvals", "list"],
    ["approvals", "get", "approval-1"],
    [
        "approvals", "decide", "run-1", "approval-1", "approve",
        "--expected-sequence", "2", "--binding-digest", SHA,
        "--reason-code", "reviewed", "--yes",
    ],
    ["promote", "package-1", "--digest", SHA, "--canary", "--yes"],
])
def test_network_commands(
    arguments: list[str], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "_client", lambda _args: FakeClient())
    assert cli.main(["--json", *arguments]) == 0
    output = capsys.readouterr().out.strip().splitlines()
    assert json.loads(output[-1])


def test_publish_and_sign(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = scaffold("tool", "sample-tool", tmp_path)
    archive = Path(package_extension(root)["path"])
    monkeypatch.setattr(cli, "_client", lambda _args: FakeClient())
    assert cli.main(["--json", "publish", str(archive), "--stage", "--yes"]) == 0
    assert json.loads(capsys.readouterr().out.strip().splitlines()[-1])["stage"] == "staging"
    monkeypatch.setattr(cli.shutil, "which", lambda _name: "/usr/bin/true")
    monkeypatch.setattr(
        cli.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0),
    )
    assert cli.main(["--json", "sign", str(archive)]) == 0


def test_doctor_and_confirmation_cancel(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "_store", lambda _args: SimpleNamespace(load=lambda: None))
    monkeypatch.setattr(cli.httpx, "get", lambda *_args, **_kwargs: SimpleNamespace(
        status_code=200, json=lambda: {"info": {"version": "2026-08-24"}}
    ))
    assert cli.main(["--json", "doctor"]) == 0
    assert json.loads(capsys.readouterr().out)["api_reachable"] is True
    monkeypatch.setattr(cli, "_client", lambda _args: FakeClient())
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: False)
    assert cli.main(["--json", "runs", "stop", "run-1", "--expected-sequence", "2"]) == 2


@pytest.mark.parametrize(
    "kind", ["skill", "connector", "evaluator", "model-profile", "agent-bundle"]
)
def test_all_scaffold_kinds(kind: str, tmp_path: Path) -> None:
    root = scaffold(kind, f"sample-{kind}", tmp_path)
    assert (root / "geyser-package.json").is_file()
