#!/usr/bin/env python3
"""Build one standalone CLI archive for the current platform."""

# ruff: noqa: S603, S607 - all executables and arguments are fixed local release inputs

from __future__ import annotations

import argparse
import gzip
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "release" / "cli_entry.py"
README = ROOT / "release" / "README.txt"
LICENSE = ROOT / "LICENSE"
BUILD_ROOT = ROOT / ".release-build"
SUPPORTED = {("Darwin", "arm64"): "darwin-arm64", ("Linux", "x86_64"): "linux-amd64"}


def source_epoch() -> int:
    value = os.environ.get("SOURCE_DATE_EPOCH")
    if value:
        return int(value)
    completed = subprocess.run(
        ["git", "show", "-s", "--format=%ct", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return int(completed.stdout.strip())


def version() -> str:
    import tomllib

    cli = tomllib.loads((ROOT / "cli" / "pyproject.toml").read_text(encoding="utf-8"))
    return str(cli["project"]["version"])


def build_executable(pass_name: str, epoch: int) -> Path:
    # Build the selected source once, then exercise and archive those bytes.
    build_dir = BUILD_ROOT / "workspace"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)
    environment = {
        **os.environ,
        "PYTHONHASHSEED": "0",
        "SOURCE_DATE_EPOCH": str(epoch),
    }
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            "--onefile",
            "--name",
            "geyser",
            "--distpath",
            os.fspath(build_dir / "dist"),
            "--workpath",
            os.fspath(build_dir / "work"),
            "--specpath",
            os.fspath(build_dir),
            "--collect-all",
            "geyser_cli",
            "--collect-all",
            "geyser_sdk",
            os.fspath(ENTRY),
        ],
        cwd=ROOT,
        env=environment,
        check=True,
    )
    executable = build_dir / "dist" / "geyser"
    if not executable.is_file():
        raise RuntimeError(f"PyInstaller did not create {executable}")
    subprocess.run(
        [os.fspath(executable), "--json", "version"],
        cwd=ROOT,
        env={**environment, "GEYSER_API_URL": "http://127.0.0.1:1"},
        check=True,
        capture_output=True,
    )
    if platform.system() == "Darwin":
        subprocess.run(["codesign", "--force", "--sign", "-", os.fspath(executable)], check=True)
        subprocess.run(["codesign", "--verify", "--verbose=2", os.fspath(executable)], check=True)
    smoke_executable(executable, environment)
    snapshot = BUILD_ROOT / pass_name / "geyser"
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(executable, snapshot)
    snapshot.chmod(0o755)
    return snapshot


def smoke_executable(executable: Path, environment: dict[str, str]) -> None:
    """Exercise the produced CLI, including actual bounded handler execution."""
    with tempfile.TemporaryDirectory(prefix="geyser-standalone-smoke-") as directory:
        root = Path(directory).resolve()
        environment = {**environment, "PATH": str(Path(sys.executable).resolve().parent)
                       + os.pathsep + environment.get("PATH", "")}

        def invoke(*args: str, succeeds: bool = True) -> subprocess.CompletedProcess[str]:
            result = subprocess.run(
                [str(executable), "--json", *args], cwd=root, env=environment,
                capture_output=True, text=True, timeout=30, check=False,
            )
            if (result.returncode == 0) != succeeds:
                raise RuntimeError("standalone functional smoke failed at " + args[0])
            return result

        invoke("init", "tool", "word-count", "--output", str(root))
        package = root / "word-count"
        tested = json.loads(invoke("test", str(package)).stdout)
        if tested["passed"] != 2 or tested["failed"]:
            raise RuntimeError("standalone handler cases did not pass")
        if json.loads(invoke("dev", str(package)).stdout)["result"] != {"word_count": 2}:
            raise RuntimeError("standalone handler returned an unexpected result")
        outside = root / "outside-package"
        outside.write_text("synthetic private value")
        (package / "handler.py").write_text(
            f"def run(value): return {{'word_count': len(open({str(outside)!r}).read())}}\n"
        )
        denied = invoke("dev", str(package), succeeds=False)
        if "extension failed inside the sandbox" not in denied.stdout:
            raise RuntimeError("standalone file boundary was not exercised")
        print("PASS standalone init/test/dev and package file boundary")


def write_archive(executable: Path, target: Path, epoch: int) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=epoch) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for source, name, mode in (
                    (executable, "geyser", 0o755),
                    (README, "README.txt", 0o644),
                    (LICENSE, "LICENSE", 0o644),
                ):
                    info = archive.gettarinfo(os.fspath(source), arcname=name)
                    info.uid = info.gid = 0
                    info.uname = info.gname = "root"
                    info.mtime = epoch
                    info.mode = mode
                    with source.open("rb") as handle:
                        archive.addfile(info, handle)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    system_machine = (platform.system(), platform.machine())
    target = SUPPORTED.get(system_machine)
    if not target:
        raise SystemExit(f"unsupported standalone target: {system_machine[0]} {system_machine[1]}")
    epoch = source_epoch()
    executable = build_executable("build", epoch)
    archive = BUILD_ROOT / "build" / f"geyser-open-{version()}-{target}.tar.gz"
    write_archive(executable, archive, epoch)
    output = args.output_dir.resolve() / archive.name
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(archive, output)
    print(f"built {output.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
