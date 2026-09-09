import json

import httpx
import pytest
from geyser_sdk import AsyncGeyserClient, GeyserClient, ReplayCreate, TaskCreate
from geyser_sdk.bundles import TaskBundle, overlay_descriptor, overlay_preview
from geyser_sdk.replay import ToolStubs


def test_bundle_applies_actual_contents_and_reports_reference_omissions():
    bundle = TaskBundle.model_validate(
        {
            "name": "support-review",
            "persona": "Explain uncertainties.",
            "skills": [
                {
                    "name": "check-facts",
                    "description": "Review evidence",
                    "instructions": "Cite supplied facts.",
                }
            ],
            "context": [
                {
                    "title": "Prior decisions",
                    "source": "synthetic:ticket-1",
                    "kind": "history",
                    "content": "The request was deferred.",
                }
            ],
            "references": [{"kind": "artifact", "ref": "synthetic:missing-file"}],
        }
    )
    projected = overlay_preview(bundle, {})
    assert [value["kind"] for value in projected["applied"]] == ["persona", "skill", "context"]
    assert all(value["digest"].startswith("sha256:") for value in projected["applied"])
    assert projected["omitted"] == [
        {
            "kind": "artifact",
            "ref": "synthetic:missing-file",
            "reason": "reference_only_not_restored",
        }
    ]
    assert projected["permissions_granted"] == []
    assert projected["shared_settings_changed"] is False


def test_bundle_reference_selection_requires_current_exact_binding(tmp_path):
    root = tmp_path
    (root / "model-profile.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "model_ref": "open:qualified-model",
                "model_profile_digest": "sha256:" + "1" * 64,
                "policy_ref": "policy:current",
            }
        )
    )
    bundle = overlay_descriptor(
        root, {"name": "qualified-profile", "kind": "model-profile", "permissions": []}
    )
    binding = {
        "model_ref": "open:qualified-model",
        "model_profile_digest": "sha256:" + "1" * 64,
        "policy_ref": "policy:current",
    }
    assert overlay_preview(bundle, binding)["selection"]["model_ref"] == binding["model_ref"]
    for key in binding:
        with pytest.raises(ValueError, match="unavailable"):
            overlay_preview(bundle, {**binding, key: "changed"})


def test_bundle_does_not_accept_permissions_sessions_or_duplicate_skills(tmp_path):
    for field in ("permissions", "provider_session", "credentials"):
        with pytest.raises(ValueError):
            TaskBundle.model_validate({"name": "bounded-bundle", field: {"value": "synthetic"}})
    skill = {"name": "same-skill", "description": "Synthetic", "instructions": "Review input"}
    with pytest.raises(ValueError, match="unique"):
        TaskBundle(name="bounded-bundle", skills=[skill, skill])
    with pytest.raises(ValueError, match="128 KiB"):
        TaskBundle(
            name="bounded-bundle",
            context=[
                {
                    "title": str(index),
                    "source": "synthetic:notes",
                    "content": "a" * 32000,
                }
                for index in range(5)
            ],
        )
    with pytest.raises(ValueError, match="permissions"):
        overlay_descriptor(
            tmp_path, {"kind": "skill", "name": "test-skill", "permissions": ["new-tool"]}
        )


def test_tool_stubs_require_exact_unambiguous_declared_replies():
    value = {
        "schema_version": 1,
        "tools": [
            {"name": "lookup", "description": "Synthetic lookup", "parameters": {"type": "object"}}
        ],
        "replies": [
            {
                "tool_name": "lookup",
                "args_digest": "sha256:" + "1" * 64,
                "result": {"status": "open"},
            }
        ],
    }
    assert ToolStubs.model_validate(value).replies[0].result == {"status": "open"}
    with pytest.raises(ValueError, match="unique"):
        ToolStubs.model_validate({**value, "replies": value["replies"] * 2})
    with pytest.raises(ValueError, match="declared"):
        ToolStubs.model_validate(
            {**value, "replies": [{**value["replies"][0], "tool_name": "missing"}]}
        )


def test_replay_budget_and_task_bundle_fields_are_typed():
    with pytest.raises(ValueError, match="budget"):
        ReplayCreate(
            fork_key="replay-key-1",
            expected_sequence=1,
            mode="model_only",
            budget={"max_cost_usd": -1},
        )
    request = TaskCreate(
        input_ref="synthetic:input",
        input_digest="sha256:" + "1" * 64,
        bundle_package_id="pkg_bundle",
        skill_package_ids=["pkg_skill"],
    )
    assert request.bundle_package_id == "pkg_bundle"


@pytest.mark.asyncio
async def test_sync_and_async_replay_use_conditional_idempotent_task_api():
    seen = []

    def respond(request):
        seen.append(request)
        return httpx.Response(
            201,
            json={
                "api_version": "2026-08-24",
                "task": {
                    "id": "task_child",
                    "project_id": "prj_current",
                    "agent_name": "Builder",
                    "input_ref": "synthetic:input",
                    "input_digest": "sha256:" + "1" * 64,
                    "spec": {"_replay": {"parent_run_id": "run_parent"}},
                    "state": "queued",
                    "run_id": "run_child",
                    "version": 1,
                    "created_at": 1,
                    "updated_at": 1,
                },
            },
        )

    value = ReplayCreate(fork_key="replay-key-1", expected_sequence=7, mode="model_only")
    transport = httpx.MockTransport(respond)
    with GeyserClient(
        "https://cell.example.test", "synthetic-token", transport=transport
    ) as client:
        assert client.replay("run_parent", value).task.id == "task_child"
    async with AsyncGeyserClient(
        "https://cell.example.test", "synthetic-token", transport=transport
    ) as client:
        assert (await client.replay("run_parent", value)).task.id == "task_child"
    assert len(seen) == 2
    for request in seen:
        assert request.url.path == "/api/v1/customer/runs/run_parent/replays"
        assert request.headers["If-Match"] == '"run-v7"'
        assert request.headers["Idempotency-Key"] == "replay-key-1"
