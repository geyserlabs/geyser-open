"""Fail CI when tracked source contains a recognizable live-secret shape."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "private key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(
        rb"\b(?:gh[pousr]_[A-Za-z0-9]{36,255}|github_pat_[A-Za-z0-9_]{60,255})\b"),
    "AWS access key": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "OpenAI API key": re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,255}\b"),
    "Google API key": re.compile(rb"\bAIza[0-9A-Za-z_-]{35}\b"),
}


def main() -> None:
    git = shutil.which("git")
    if git is None:
        raise SystemExit("secret scan requires git")
    output = subprocess.check_output(  # noqa: S603 -- resolved fixed git executable
        [git, "ls-files", "-z"], cwd=ROOT)
    findings: list[str] = []
    for raw_path in output.split(b"\0"):
        if not raw_path:
            continue
        relative = raw_path.decode("utf-8", errors="strict")
        path = ROOT / relative
        if not path.is_file() or path.stat().st_size > 5 * 1024 * 1024:
            continue
        data = path.read_bytes()
        if b"\0" in data:
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(data):
                findings.append(f"{relative}: recognizable {label}")
    if findings:
        raise SystemExit("secret scan failed:\n" + "\n".join(sorted(findings)))
    print("secret scan: tracked source contains no recognized credential shapes")


if __name__ == "__main__":
    main()
