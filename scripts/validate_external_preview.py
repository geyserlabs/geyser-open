#!/usr/bin/env python3
"""Validate a content-safe external developer preview receipt."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from conformance.developer_preview import validate_preview_receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    value = json.loads(args.receipt.read_text(encoding="utf-8"))
    checked = validate_preview_receipt(value)
    print(json.dumps({
        "validated": True,
        "receipt_digest": checked["receipt_digest"],
        "release_version": checked["release"]["version"],
        "defects_closed": len(checked["defects"]),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
