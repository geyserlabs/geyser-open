from __future__ import annotations

from typing import Any

import httpx
import pytest
from geyser_sdk import (
    ApprovalDecision,
    AsyncGeyserClient,
    CancelRequest,
    EvaluationCreate,
    ForkCreate,
    GeyserClient,
    PackagePromotion,
    PackageUpload,
    ProblemError,
    TaskCreate,
    TaskResponse,
    TransportError,
)

SHA = "sha256:" + "a" * 64


def task_value() -> dict[str, Any]:
    return {
        "id": "task-1",
        "project_id": "project-1",
        "agent_name": "Ada",
        "input_ref": "artifact:prompt",
        "input_digest": SHA,
        "spec": {},
        "state": "completed",
        "run_id": "run-1",
        "version": 1,
        "created_at": 1,
        "updated_at": 2,
    }


def run_value() -> dict[str, Any]:
    return {
        "id": "run-1",
        "task_id": "task-1",
        "state": "completed",
        "sequence": 2,
        "agent_name": "Ada",
        "framework": "open",
        "backend": "open-harness",
        "model_ref": "qualified:model",
        "runtime_profile_digest": SHA,
        "model_profile_digest": SHA,
        "qualification_evidence_digest": SHA,
        "usage": {},
        "budget_enforcement": {},
        "effect_count": 0,
        "approval_count": 0,
        "artifact_count": 0,
        "evaluation_count": 0,
        "created_at": 1,
        "updated_at": 2,
    }


def response_for(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    common = {"api_version": "2026-08-24"}
    if path.endswith("/capabilities"):
        return httpx.Response(200, json={**common, "capability_profile": {
            "agent_name": "Ada",
            "framework": "open",
            "backend": "open-harness",
            "adapter_id": "open",
            "adapter_version": "1",
            "runtime_profile_digest": SHA,
            "model_profile_digest": SHA,
            "qualification_evidence_digest": SHA,
            "capabilities": {"durable_run": "native"},
        }})
    if "/approvals/" in path and request.method == "GET":
        return httpx.Response(200, json={**common, "approval": {
            "approval_id": "approval-1", "state": "requested"
        }})
    if path.endswith("/approvals"):
        return httpx.Response(200, json={**common, "data": [], "next_cursor": ""})
    if path.endswith("/events"):
        return httpx.Response(200, json={
            **common,
            "data": [{
                "sequence": 2,
                "event_type": "run.completed",
                "event_id": "event-2",
                "observed_at": 2,
                "created_at": 2,
                "data": {},
                "digest": SHA,
            }],
            "next_cursor": "",
            "current_sequence": 2,
        })
    if path.endswith("/trace"):
        return httpx.Response(200, json={**common, "trace": {
            "trace_id": "trace-1",
            "run_id": "run-1",
            "state": "completed",
            "framework": "open",
            "model_ref": "qualified:model",
            "visibility": "customer",
            "started_at": 1,
            "finished_at": 2,
            "duration_ms": 1000,
            "usage": {},
            "usage_precision": "exact",
            "budget_enforcement": {},
            "effect_count": 0,
            "approval_count": 0,
            "artifact_count": 0,
            "evaluation_count": 0,
            "spans": [],
            "trace_digest": SHA,
        }})
    if "/runs" in path:
        if path.endswith("/runs") and request.method == "GET":
            return httpx.Response(200, json={**common, "data": [run_value()], "next_cursor": ""})
        return httpx.Response(200, json={**common, "run": run_value()})
    if "/packages/" in path:
        return httpx.Response(200, json={**common, "package": {
            "package_id": "package-1", "name": "sample", "version": "0.1.0",
            "digest": SHA, "stage": "canary", "status": "active"
        }})
    if path.endswith("/packages"):
        if request.method == "GET":
            return httpx.Response(200, json={**common, "data": [], "next_cursor": ""})
        return httpx.Response(200, json={**common, "package": {
            "package_id": "package-1", "name": "sample", "version": "0.1.0",
            "digest": SHA, "stage": "staging", "status": "uploaded"
        }})
    if path.endswith("/tasks") and request.method == "GET":
        return httpx.Response(200, json={**common, "data": [task_value()], "next_cursor": ""})
    return httpx.Response(200, json={**common, "task": task_value()})


def test_sync_semantic_surface_and_headers() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return response_for(request)

    with GeyserClient(
        "https://api.example", "dev-token", transport=httpx.MockTransport(handler)
    ) as client:
        create = client.create_task(
            TaskCreate(input_ref="artifact:prompt", input_digest=SHA),
            idempotency_key="create-1",
        )
        assert create.task.id == client.get_task("task-1").task.id
        assert [item.id for item in client.iter_tasks()] == ["task-1"]
        assert client.capabilities(agent_name="Ada").capability_profile.framework == "open"
        assert [item.id for item in client.iter_runs()] == ["run-1"]
        assert client.get_run("run-1", customer=True).run.state == "completed"
        assert [event.event_type for event in client.watch_events("run-1")] == ["run.completed"]
        assert client.trace("run-1").trace.usage_precision == "exact"
        assert client.list_approvals().data == []
        assert client.get_approval("approval-1").approval.state == "requested"
        assert client.list_packages().data == []
        client.upload_package(
            PackageUpload(
                name="sample", version="0.1.0", digest=SHA,
                media_type="application/zip", content_base64="eA=="
            ),
            idempotency_key=SHA,
        )
        client.promote_package(
            "package-1",
            PackagePromotion(promotion_id="promotion-1", target="canary", expected_digest=SHA),
        )
        client.cancel_run(
            "run-1",
            CancelRequest(
                cancellation_id="cancel-1", expected_sequence=2, reason_code="test"
            ),
        )
        client.evaluate("run-1", EvaluationCreate(
            evaluation_id="eval-1", expected_sequence=2, evaluator_ref="eval:test",
            verdict="pass", score=1,
        ))
        client.fork("run-1", ForkCreate(
            fork_id="fork-1", child_run_id="run-2", expected_sequence=2, reason_code="test"
        ))
        client.decide_approval("run-1", "approval-1", ApprovalDecision(
            decision_id="decision-1", decision="approve", expected_approval_sequence=2,
            binding_digest=SHA, reason_code="test",
        ))
    assert all(request.headers["authorization"] == "Bearer dev-token" for request in requests)
    assert any(request.headers.get("idempotency-key") == "create-1" for request in requests)
    assert any(request.headers.get("if-match") == '"run-v2"' for request in requests)
    assert any(
        request.url.path.endswith("/events")
        and request.url.params.get("cursor") == "0"
        for request in requests
    )


@pytest.mark.asyncio
async def test_async_surface_and_safe_retry() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        if request.url.path.endswith("/tasks") and request.method == "GET":
            attempts += 1
            if attempts == 1:
                return httpx.Response(503, json={"code": "busy"})
        return response_for(request)

    async with AsyncGeyserClient(
        "https://api.example", lambda: "rotating-token", transport=httpx.MockTransport(handler)
    ) as client:
        assert (await client.create_task(
            TaskCreate(input_ref="artifact:prompt", input_digest=SHA),
            idempotency_key="async-create",
        )).task.id == "task-1"
        assert (await client.get_task("task-1")).task.id == "task-1"
        assert [item.id async for item in client.iter_tasks()] == ["task-1"]
        assert attempts == 2
        assert [item.id async for item in client.iter_runs(customer=True)] == ["run-1"]
        assert [item.event_type async for item in client.watch_events("run-1")] == [
            "run.completed"
        ]
        assert (await client.capabilities(agent_name="Ada")).capability_profile.backend
        assert (await client.trace("run-1", customer=True)).trace.trace_id == "trace-1"
        assert (await client.list_approvals()).data == []
        assert (await client.get_approval("approval-1")).approval.approval_id == "approval-1"
        assert (await client.list_packages()).data == []
        await client.upload_package(
            PackageUpload(
                name="sample", version="0.1.0", digest=SHA,
                media_type="application/zip", content_base64="eA==",
            ),
            idempotency_key=SHA,
        )
        await client.promote_package(
            "package-1",
            PackagePromotion(
                promotion_id="promotion-1", target="canary", expected_digest=SHA
            ),
        )
        await client.cancel_run(
            "run-1",
            CancelRequest(
                cancellation_id="cancel-1", expected_sequence=2, reason_code="test"
            ),
        )
        await client.evaluate(
            "run-1",
            EvaluationCreate(
                evaluation_id="eval-1", expected_sequence=2,
                evaluator_ref="eval:test", verdict="pass", score=1,
            ),
        )
        await client.fork(
            "run-1",
            ForkCreate(
                fork_id="fork-1", child_run_id="run-2",
                expected_sequence=2, reason_code="test",
            ),
        )
        await client.decide_approval(
            "run-1",
            "approval-1",
            ApprovalDecision(
                decision_id="decision-1", decision="approve",
                expected_approval_sequence=2, binding_digest=SHA, reason_code="test",
            ),
        )


def test_problem_details_invalid_json_and_unsafe_retry() -> None:
    def problem(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(409, json={
            "type": "https://docs.example/problems/conflict",
            "title": "Conflict",
            "status": 409,
            "detail": "sequence changed",
            "code": "sequence_conflict",
            "current_version": 4,
        })

    client = GeyserClient("https://api.example", "token", transport=httpx.MockTransport(problem))
    with pytest.raises(ProblemError) as caught:
        client.get_task("task-1")
    assert caught.value.problem.current_version == 4
    client.close()

    calls = 0

    def broken(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ConnectError("offline")

    client = GeyserClient("https://api.example", "token", transport=httpx.MockTransport(broken))
    with pytest.raises(TransportError):
        client._request("POST", "/unsafe", TaskResponse)
    assert calls == 1
    client.close()


def test_client_rejects_insecure_remote_and_missing_idempotency() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        GeyserClient("http://api.example", "token")
    with GeyserClient(
        "http://localhost:8000", "token", transport=httpx.MockTransport(response_for)
    ) as client:
        with pytest.raises(ValueError, match="idempotency"):
            client.create_task(
                TaskCreate(input_ref="artifact:x", input_digest=SHA), idempotency_key=""
            )
