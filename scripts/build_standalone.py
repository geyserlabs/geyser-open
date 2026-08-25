#!/usr/bin/env python3
"""Build and byte-compare deterministic standalone CLI archives."""

# ruff: noqa: S603, S607 - all executables and arguments are fixed local release inputs

from __future__ import annotations

import argparse
import gzip
import hashlib
import os
import platform
import shutil
import subprocess
import sys
import tarfile
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
    # PyInstaller records portions of its work path in collected bytecode.
    # Reuse one exact path for both independent builds, then snapshot the
    # executable, so the byte comparison detects inputs rather than paths.
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
    snapshot = BUILD_ROOT / pass_name / "geyser"
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(executable, snapshot)
    snapshot.chmod(0o755)
    return snapshot


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


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    system_machine = (platform.system(), platform.machine())
    target = SUPPORTED.get(system_machine)
    if not target:
        raise SystemExit(f"unsupported standalone target: {system_machine[0]} {system_machine[1]}")
    epoch = source_epoch()
    # A fresh Python environment can populate deterministic import bytecode on
    # its first PyInstaller analysis, changing only base_library.zip ordering.
    # Discard one warm-up executable, then compare two independent clean builds.
    build_executable("warmup", epoch)
    archives: list[Path] = []
    for pass_name in ("first", "second"):
        executable = build_executable(pass_name, epoch)
        archive = BUILD_ROOT / pass_name / f"geyser-open-{version()}-{target}.tar.gz"
        write_archive(executable, archive, epoch)
        archives.append(archive)
    first_digest, second_digest = (digest(path) for path in archives)
    if first_digest != second_digest:
        raise SystemExit(
            f"standalone build is not reproducible: {first_digest} != {second_digest}"
        )
    output = args.output_dir.resolve() / archives[0].name
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(archives[0], output)
    print(f"built reproducible {output.name} sha256:{first_digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
