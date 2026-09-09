"""Exercise CLI commands through the real SDK encoding/decoding boundary."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
from geyser_cli import __main__ as cli
from geyser_sdk import AsyncGeyserClient, GeyserClient
from geyser_sdk.models import InputCreate

SHA = "sha256:" + "a" * 64


def workflow_transport(
    requests: list[httpx.Request], state: str = "completed"
) -> httpx.MockTransport:
    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        path = request.url.path
        if path.endswith("/inputs"):
            body = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "input": {
                        "ref": "gdev:dobj_" + "a" * 64,
                        "digest": SHA,
                        "kind": body["kind"],
                        "size_bytes": 10,
                    }
                },
            )
        if path.endswith("/result"):
            return httpx.Response(
                200,
                json={
                    "result": {
                        "ref": "gdev:dobj_" + "b" * 64,
                        "digest": SHA,
                        "kind": "result",
                        "size_bytes": 10,
                        "value": {"answer": 42},
                    }
                },
            )
        if request.method == "DELETE":
            assert request.headers["if-match"] == '"' + SHA + '"'
            return httpx.Response(200, json={"revoked": True})
        task = {
            "id": "task-1",
            "project_id": "project-1",
            "agent_name": "Builder",
            "input_ref": "gdev:dobj_" + "a" * 64,
            "input_digest": SHA,
            "spec": {},
            "state": state,
            "run_id": "run-1",
            "version": 2,
            "created_at": 1,
            "updated_at": 2,
        }
        if path.endswith("/tasks") and request.method == "GET":
            return httpx.Response(200, json={"data": [task]})
        if request.method == "POST":
            body = json.loads(request.content)
            assert body["budget"]["max_cost_usd"] == 0.25
            assert request.headers["idempotency-key"] == "workflow-123"
            assert body["metadata"] == {"execution": "extension", "package_id": "pkg-test"}
        return httpx.Response(200, json={"task": task})

    return httpx.MockTransport(handle)


def test_cli_real_sdk_task_lifecycle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    requests: list[httpx.Request] = []
    monkeypatch.setattr(
        cli,
        "_client",
        lambda _: GeyserClient(
            "https://api.example/cell/2", "test", transport=workflow_transport(requests)
        ),
    )
    source = tmp_path / "input.json"
    source.write_text('{"text": "hello"}')
    contract = tmp_path / "contract.json"
    contract.write_text('{"schema_version":1,"schema_ref":"test:1","json_schema":{}}')
    assert (
        cli.main(
            [
                "--json",
                "tasks",
                "create",
                "--input",
                str(source),
                "--contract",
                str(contract),
                "--max-cost",
                "0.25",
                "--package",
                "pkg-test",
                "--idempotency-key",
                "workflow-123",
            ]
        )
        == 0
    )
    assert len(requests) == 3
    assert all(request.url.path.startswith("/cell/2/api/v1/") for request in requests)
    for action in ("get", "result", "wait"):
        assert cli.main(["--json", "tasks", action, "task-1"]) == 0
    assert cli.main(["--json", "tasks", "list"]) == 0
    assert cli.main(["--json", "revoke", "pkg-test", "--digest", SHA, "--yes"]) == 0
    assert all(json.loads(line) for line in capsys.readouterr().out.splitlines())


def test_wait_failure_timeout_and_invalid_bound(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    requests: list[httpx.Request] = []
    state = {"value": "failed"}
    monkeypatch.setattr(
        cli,
        "_client",
        lambda _: GeyserClient(
            "https://api.example", "test", transport=workflow_transport(requests, state["value"])
        ),
    )
    assert cli.main(["--json", "tasks", "wait", "task-1"]) == 0
    assert json.loads(capsys.readouterr().out)["result"] is None
    assert not any(request.url.path.endswith("/result") for request in requests)
    assert cli.main(["--json", "tasks", "wait", "task-1", "--timeout", "0"]) == 2
    capsys.readouterr()
    state["value"] = "claimed"
    times = iter([0.0, 0.0, 0.0, 2.0])
    monkeypatch.setattr(cli.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(cli.time, "sleep", lambda _: None)
    assert cli.main(["--json", "tasks", "wait", "task-1", "--timeout", "1"]) == 2
    assert "continues remotely" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_async_owned_inputs_results_and_revocation() -> None:
    requests: list[httpx.Request] = []
    async with AsyncGeyserClient(
        "https://api.example", "test", transport=workflow_transport(requests)
    ) as client:
        assert (await client.upload_input(InputCreate(value={}))).input.digest == SHA
        assert (await client.result("task-1")).result.value == {"answer": 42}
        assert (await client.revoke_package("pkg-test", expected_digest=SHA)).revoked
        with pytest.raises(ValueError):
            await client.revoke_package("pkg-test", expected_digest="not-a-digest")


def test_invalid_cli_budget_does_not_upload_input(tmp_path, monkeypatch, capsys):
    def unexpected(_args):
        raise AssertionError("invalid budgets must fail before constructing a network client")

    monkeypatch.setattr(cli, "_client", unexpected)
    assert (
        cli.main(
            [
                "--json",
                "tasks",
                "create",
                "--input",
                str(tmp_path / "missing.json"),
                "--idempotency-key",
                "invalid-task",
                "--max-cost",
                "-1",
            ]
        )
        == 2
    )
    assert "budget" in capsys.readouterr().out
