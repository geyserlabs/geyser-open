"""Fail CI when tracked source contains a recognizable live-secret shape."""

from __future__ import annotations

import re
import shutil
import subprocess
from collections.abc import Iterable
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
SNAPSHOT_EXCLUDES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".release-build",
    ".release-python",
    "release-standalone",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
    "release-assets",
    "site",
}


def source_paths(git: str | None) -> Iterable[Path]:
    if git is not None and (ROOT / ".git").exists():
        output = subprocess.check_output(  # noqa: S603 -- resolved fixed git executable
            [git, "ls-files", "-z"], cwd=ROOT
        )
        for raw_path in output.split(b"\0"):
            if raw_path:
                yield Path(raw_path.decode("utf-8", errors="strict"))
        return
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if path.is_file() and not any(part in SNAPSHOT_EXCLUDES for part in relative.parts):
            yield relative


def main() -> None:
    git = shutil.which("git")
    findings: list[str] = []
    for relative_path in source_paths(git):
        relative = relative_path.as_posix()
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
    mode = "tracked source" if git is not None and (ROOT / ".git").exists() else "source snapshot"
    print(f"secret scan: {mode} contains no recognized credential shapes")


if __name__ == "__main__":
    main()
