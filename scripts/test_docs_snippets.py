#!/usr/bin/env python3
"""Execute the credential-free commands displayed by the public quickstart."""

# ruff: noqa: S603 - fixed, credential-free documentation commands

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="geyser-docs-") as temporary:
        root = Path(temporary)
        commands = [
            [
                sys.executable,
                "-m",
                "geyser_cli",
                "init",
                "tool",
                "word-count",
                "--output",
                str(root),
            ],
            [sys.executable, "-m", "geyser_cli", "validate", str(root / "word-count")],
            [sys.executable, "-m", "geyser_cli", "test", str(root / "word-count")],
            [sys.executable, "-m", "geyser_cli", "dev", str(root / "word-count")],
            [sys.executable, "examples/emulator_quickstart.py"],
            [sys.executable, "examples/extension_app.py", "issue-normalizer"],
            [sys.executable, "examples/extension_app.py", "source-review-gate"],
        ]
        for command in commands:
            subprocess.run(command, check=True)
    print("documentation snippets passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
