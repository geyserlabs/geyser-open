from pathlib import Path

from geyser_cli.extensions import test_extension as execute_cases
from geyser_sdk.extensions import run_extension

ROOT = Path(__file__).resolve().parents[1] / "examples/packages"


def test_issue_normalization_and_critical_input() -> None:
    root = ROOT / "issue-normalizer"
    assert execute_cases(root)["failed"] == []
    assert (
        run_extension(
            root, {"number": 7, "title": "Question", "body": "Details", "labels": ["question"]}
        )["category"]
        == "question"
    )


def test_review_gate_rejects_missing_and_invented_citations() -> None:
    root = ROOT / "source-review-gate"
    assert execute_cases(root)["failed"] == []
    assert run_extension(
        root, {"source_ids": ["source:1"], "claims": [{"text": "x", "source_ids": []}]}
    ) == {"passed": False, "unsupported_claims": [0]}


def test_support_workflow_preserves_sources_and_rejects_invented_citations(monkeypatch):
    import importlib
    import json

    monkeypatch.syspath_prepend(str(ROOT.parent))
    application = importlib.import_module("support_escalation")
    operations = []

    def execute(value, *, contract, operation_id, package_id="", timeout=300):
        operations.append(operation_id)
        if package_id:
            result = run_extension(ROOT / package_id, value)
        else:
            assert value["sources"][0]["source_id"] == "ticket:42"
            assert value["sources"][1]["source_id"] == "account:42"
            result = {
                "summary": "A synthetic draft.",
                "claims": [{"text": "Unsupported", "source_ids": ["invented:99"]}],
            }
        return {"result": result, "task_id": operation_id, "run_id": "run:" + operation_id}

    monkeypatch.setattr(application, "submit", execute)
    ticket = json.loads((ROOT / "issue-normalizer/example-input.json").read_text())
    ticket["number"] = 42
    result = application.investigate(
        ticket,
        [{"source_id": "account:42", "text": "Synthetic evidence"}],
        operation_id="support:42",
        normalizer_package="issue-normalizer",
        review_package="source-review-gate",
    )
    assert result["human_review_required"] is True
    assert result["citation_coverage"] == {"passed": False, "unsupported_claims": [0]}
    assert result["tasks"] == [
        "support:42:normalize",
        "support:42:investigate",
        "support:42:review",
    ]
