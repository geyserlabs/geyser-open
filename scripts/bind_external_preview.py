#!/usr/bin/env python3
"""Canonically bind an unsigned external developer preview receipt."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from conformance.developer_preview import validate_preview_receipt
from conformance.qualification import bind_receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path, help="unsigned JSON receipt")
    args = parser.parse_args()
    value = json.loads(args.receipt.read_text(encoding="utf-8"))
    if "receipt_digest" in value:
        raise SystemExit("input is already bound; validate it instead")
    bound = bind_receipt(value)
    validate_preview_receipt(bound)
    print(json.dumps(bound, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
