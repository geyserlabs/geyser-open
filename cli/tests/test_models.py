from __future__ import annotations

import json
from typing import Any

import pytest
from geyser_cli import __main__ as cli
from geyser_cli.output import table
from geyser_sdk import Problem, ProblemError, WorkspaceModelList


class ModelsClient:
    def __init__(self, listed: dict[str, Any] | Exception) -> None:
        self.listed = listed

    def __enter__(self) -> ModelsClient:
        return self

    def __exit__(self, *_args: object) -> None:
        pass

    def list_models(self) -> WorkspaceModelList:
        if isinstance(self.listed, Exception):
            raise self.listed
        return WorkspaceModelList.model_validate(self.listed)

    def openai_base_url(self) -> str:
        return "https://cell.example/api/v1/openai"


LISTED = {
    "object": "list",
    "data": [
        {
            "id": "private/pmd_support_v2",
            "object": "model",
            "created": 1790000000,
            "owned_by": "geyser",
            "geyser": {
                "display_name": "Support replies",
                "state": "running",
                "context_window": 32768,
            },
        },
        {
            "id": "private/pmd_triage_v1",
            "object": "model",
            "created": 1790000100,
            "owned_by": "geyser",
            "geyser": {"display_name": "Triage", "state": "stopped", "context_window": 8192},
        },
    ],
}


def test_models_list_table(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "_client", lambda _args: ModelsClient(LISTED))
    assert cli.main(["models", "list"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].split() == ["ID", "NAME", "STATE", "CONTEXT"]
    assert lines[1].split()[0] == "private/pmd_support_v2"
    assert lines[1].index("Support") == lines[0].index("NAME")
    assert lines[2].split()[-2:] == ["stopped", "8192"]
    assert lines[-1] == "OpenAI base URL: https://cell.example/api/v1/openai"


def test_models_list_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "_client", lambda _args: ModelsClient(LISTED))
    assert cli.main(["--json", "models", "list"]) == 0
    value = json.loads(capsys.readouterr().out)
    assert value["object"] == "list"
    assert [model["id"] for model in value["data"]] == [
        "private/pmd_support_v2",
        "private/pmd_triage_v1",
    ]
    assert value["data"][0]["geyser"]["state"] == "running"


def test_models_list_empty_explains_how_to_open_a_model(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        cli, "_client", lambda _args: ModelsClient({"object": "list", "data": []})
    )
    assert cli.main(["models", "list"]) == 0
    assert "Developer projects" in capsys.readouterr().out


def test_models_list_missing_scope_is_a_clean_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    problem = Problem.from_mapping(
        {
            "error": {
                "message": "This credential can't use models. Create one with models:infer.",
                "type": "permission_error",
                "code": "insufficient_scope",
            }
        },
        403,
    )
    monkeypatch.setattr(cli, "_client", lambda _args: ModelsClient(ProblemError(problem)))
    assert cli.main(["--json", "models", "list"]) == 2
    value = json.loads(capsys.readouterr().out)
    assert value["error"] == "ProblemError"
    assert value["detail"].startswith("insufficient_scope (403)")


def test_login_passes_models_infer_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def fake_login(_url: str, _store: object, *, scopes: list[str], **_kwargs: Any) -> Any:
        seen["scopes"] = scopes
        return {"authenticated": True}

    monkeypatch.setattr(cli, "login_device", fake_login)
    monkeypatch.setattr(cli, "_store", lambda _args: object())
    assert cli.main(["--json", "login", "--no-browser", "--scope", "models:infer"]) == 0
    assert seen["scopes"] == ["models:infer"]


def test_table_without_rows_and_control_characters() -> None:
    assert table(["ID", "NAME"], []) == "ID  NAME"
    assert table(["ID"], [["private/x\x1b[2J"]]).splitlines()[1] == "private/x?[2J"
