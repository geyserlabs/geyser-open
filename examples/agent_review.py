"""Ask a qualified Open Agent to review supplied material and return cited JSON.

This invokes your configured Agent and can incur model/compute usage. It does
not authorize external actions or fetch evidence from an arbitrary URL.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from task_workflow import submit

CONTRACT = {
    "schema_version": 1,
    "schema_ref": "example:document-review:1",
    "json_schema": {
        "type": "object",
        "required": ["summary", "claims"],
        "additionalProperties": False,
        "properties": {
            "summary": {"type": "string", "minLength": 1, "maxLength": 4000},
            "claims": {
                "type": "array",
                "minItems": 1,
                "maxItems": 30,
                "items": {
                    "type": "object",
                    "required": ["text", "source_ids"],
                    "additionalProperties": False,
                    "properties": {
                        "text": {"type": "string", "maxLength": 2000},
                        "source_ids": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 10,
                            "items": {"type": "string", "maxLength": 100},
                        },
                    },
                },
            },
        },
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("material", type=Path, help="JSON array of source_id/text objects")
    parser.add_argument("--operation-id", required=True)
    args = parser.parse_args()
    material = json.loads(args.material.read_text())
    if not isinstance(material, list) or not 1 <= len(material) <= 30:
        raise ValueError("supply 1-30 source objects")
    value = {
        "instruction": (
            "Review only the supplied material. Summarize it and attach "
            "supplied source IDs to every claim. Do not perform external actions."
        ),
        "sources": material,
    }
    print(json.dumps(submit(value, contract=CONTRACT, operation_id=args.operation_id), indent=2))


if __name__ == "__main__":
    main()
