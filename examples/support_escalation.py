"""Normalize a ticket, draft an evidence-linked response, and check citation coverage.

Requires two active packages (issue-normalizer and source-review-gate) and a
qualified Open Agent. This prepares a draft; it does not send a customer message.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agent_review import CONTRACT as REVIEW_CONTRACT
from task_workflow import submit


def package_contract(name: str, kind: str) -> dict[str, Any]:
    definition = json.loads(
        (Path(__file__).parent / "packages" / name / f"{kind}.json").read_text()
    )
    return {
        "schema_version": 1,
        "schema_ref": f"example:{name}:1",
        "json_schema": definition["output_schema"],
    }


def investigate(
    ticket: dict[str, Any],
    facts: list[dict[str, str]],
    *,
    operation_id: str,
    normalizer_package: str,
    review_package: str,
) -> dict[str, Any]:
    if (
        not isinstance(facts, list)
        or len(facts) > 29
        or any(
            not isinstance(fact, dict)
            or not isinstance(fact.get("source_id"), str)
            or not fact["source_id"]
            or not isinstance(fact.get("text"), str)
            for fact in facts
        )
    ):
        raise ValueError("supply at most 29 source_id/text fact objects")
    ticket_source = "ticket:" + str(ticket["number"])
    source_ids = [ticket_source, *(fact["source_id"] for fact in facts)]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("every supplied source must have a unique source_id")
    normalized = submit(
        ticket,
        contract=package_contract("issue-normalizer", "connector"),
        operation_id=operation_id + ":normalize",
        package_id=normalizer_package,
        timeout=30,
    )
    sources = [{"source_id": ticket_source, "text": json.dumps(normalized["result"])}, *facts]
    review = submit(
        {
            "instruction": (
                "Investigate the supplied support ticket using only these sources. In summary, "
                "explain likely causes, uncertainty, the next useful check, "
                "and a draft customer reply. "
                "Attach supplied source IDs to each factual claim. Do not send or modify anything."
            ),
            "sources": sources,
        },
        contract=REVIEW_CONTRACT,
        operation_id=operation_id + ":investigate",
    )
    gate = submit(
        {"claims": review["result"]["claims"], "source_ids": source_ids},
        contract=package_contract("source-review-gate", "evaluator"),
        operation_id=operation_id + ":review",
        package_id=review_package,
        timeout=30,
    )
    return {
        "draft": review["result"],
        "citation_coverage": gate["result"],
        "human_review_required": True,
        "tasks": [item["task_id"] for item in (normalized, review, gate)],
        "runs": [item["run_id"] for item in (normalized, review, gate)],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ticket", type=Path)
    parser.add_argument("facts", type=Path, help="JSON array of source_id/text objects")
    parser.add_argument("--operation-id", required=True)
    parser.add_argument("--normalizer-package", required=True)
    parser.add_argument("--review-package", required=True)
    args = parser.parse_args()
    result = investigate(
        json.loads(args.ticket.read_text()),
        json.loads(args.facts.read_text()),
        operation_id=args.operation_id,
        normalizer_package=args.normalizer_package,
        review_package=args.review_package,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
