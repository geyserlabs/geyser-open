"""Run a complete issue-normalization or source-review application locally or remotely."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geyser_sdk.extensions import run_extension
from task_workflow import submit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("application", choices=["issue-normalizer", "source-review-gate"])
    parser.add_argument("--input", type=Path)
    parser.add_argument("--remote-package")
    parser.add_argument("--operation-id", help="a stable business operation ID, required remotely")
    args = parser.parse_args()
    root = Path(__file__).parent / "packages" / args.application
    value = json.loads((args.input or root / "example-input.json").read_text())
    if args.remote_package:
        if not args.operation_id:
            parser.error(
                "remote execution requires --operation-id; reuse it after an interrupted request"
            )
        kind = json.loads((root / "geyser-package.json").read_text())["kind"]
        definition = json.loads((root / f"{kind}.json").read_text())
        result = submit(
            value,
            contract={
                "schema_version": 1,
                "schema_ref": f"example:{args.application}:1",
                "json_schema": definition["output_schema"],
            },
            package_id=args.remote_package,
            operation_id=args.operation_id,
            timeout=30,
        )
    else:
        result = run_extension(root, value)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
