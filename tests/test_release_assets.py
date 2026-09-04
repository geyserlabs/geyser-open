from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "release_assets.py"


def run(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - arguments are constructed by the test
        [sys.executable, str(SCRIPT), *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_workspace_versions_are_consistent() -> None:
    result = run("version")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "0.1.0"


def test_contract_archive_is_reproducible(tmp_path: Path) -> None:
    outputs = [tmp_path / "one", tmp_path / "two"]
    for output in outputs:
        result = run(
            "contracts", "--output-dir", str(output),
            "--source-epoch", "1700000000",
        )
        assert result.returncode == 0, result.stderr
    for name in ("geyser-contracts-0.1.0.tar.gz", "geyser-openapi-0.1.0.json"):
        values = [
            hashlib.sha256((directory / name).read_bytes()).hexdigest()
            for directory in outputs
        ]
        assert values[0] == values[1]
