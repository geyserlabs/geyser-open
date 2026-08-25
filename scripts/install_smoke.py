#!/usr/bin/env python3
"""Install both public distributions in a clean venv and execute the CLI."""

# ruff: noqa: S603 - fixed argv only; paths are locally resolved build artifacts

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dist", type=Path)
    args = parser.parse_args()
    sdk = next(args.dist.resolve().glob("geyser_sdk-*.whl"))
    cli = next(args.dist.resolve().glob("geyser_open-*.whl"))
    with tempfile.TemporaryDirectory(prefix="geyser-install-") as temporary:
        venv = Path(temporary) / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        python = venv / "bin" / "python"
        geyser = venv / "bin" / "geyser"
        subprocess.run([str(python), "-m", "pip", "install", str(sdk), str(cli)], check=True)
        value = subprocess.run(
            [str(geyser), "--json", "version"], check=True, capture_output=True, text=True
        )
        if "geyser_open" not in json.loads(value.stdout):
            raise SystemExit("installed CLI did not report its version")
    print("clean install smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
