#!/usr/bin/env python3
"""Prove uninstall removes both distributions and the console entry point."""

# ruff: noqa: S603 - fixed argv only; paths are locally resolved build artifacts

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dist", type=Path)
    args = parser.parse_args()
    wheels = [str(path.resolve()) for path in sorted(args.dist.glob("*.whl"))]
    with tempfile.TemporaryDirectory(prefix="geyser-uninstall-") as temporary:
        venv = Path(temporary) / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        python = venv / "bin" / "python"
        subprocess.run([str(python), "-m", "pip", "install", *wheels], check=True)
        subprocess.run(
            [str(python), "-m", "pip", "uninstall", "-y", "geyser-open", "geyser-sdk"],
            check=True,
        )
        probe = subprocess.run(
            [str(python), "-c", "import geyser_sdk"], capture_output=True, text=True
        )
        if probe.returncode == 0 or (venv / "bin" / "geyser").exists():
            raise SystemExit("uninstall left an import or console entry point")
    print("clean uninstall smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
