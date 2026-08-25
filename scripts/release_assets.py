#!/usr/bin/env python3
"""Validate and assemble retained public release records."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import tarfile
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILES = (
    ROOT / "sdk" / "python" / "pyproject.toml",
    ROOT / "cli" / "pyproject.toml",
)
GENERATED = {
    "SHA256SUMS",
    "release-manifest.json",
    "geyser-open.spdx.json",
    "geyser-open.cyclonedx.json",
    "dependency-inventory.json",
}


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def versions() -> set[str]:
    return {
        str(tomllib.loads(path.read_text(encoding="utf-8"))["project"]["version"])
        for path in VERSION_FILES
    }


def validate_source(tag: str | None = None) -> str:
    values = versions()
    if len(values) != 1:
        raise ValueError(f"SDK and CLI versions differ: {sorted(values)}")
    value = values.pop()
    expected = f"v{value}"
    if tag is not None and tag != expected:
        raise ValueError(f"release tag {tag!r} must be {expected!r}")
    sdk_init = (ROOT / "sdk" / "python" / "src" / "geyser_sdk" / "__init__.py").read_text()
    cli_init = (ROOT / "cli" / "src" / "geyser_cli" / "__init__.py").read_text()
    literal = f'__version__ = "{value}"'
    if literal not in sdk_init or literal not in cli_init:
        raise ValueError("package metadata and runtime __version__ values differ")
    if (ROOT / "schemas" / "VERSION").read_text(encoding="utf-8").strip() != "2026-08-24":
        raise ValueError("unexpected frozen schema version")
    return value


def dependency_inventory(output: Path, source_commit: str) -> None:
    lock = ROOT / "uv.lock"
    document = tomllib.loads(lock.read_text(encoding="utf-8"))
    packages = []
    for package in document["package"]:
        source = package.get("source", {})
        packages.append(
            {
                "name": package["name"],
                "version": package.get("version", "workspace"),
                "source": source,
            }
        )
    result = {
        "schema_version": 1,
        "source_commit": source_commit,
        "lockfile": "uv.lock",
        "lockfile_sha256": sha256(lock),
        "packages": sorted(packages, key=lambda item: (item["name"], item["version"])),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _tar_info(path: Path, name: str, epoch: int) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name)
    info.size = path.stat().st_size
    info.mode = 0o644
    info.mtime = epoch
    info.uid = info.gid = 0
    info.uname = info.gname = "root"
    return info


def contract_assets(output_dir: Path, epoch: int) -> None:
    value = validate_source()
    openapi_target = output_dir / f"geyser-openapi-{value}.json"
    openapi_target.write_bytes((ROOT / "openapi" / "geyser-v1.openapi.json").read_bytes())
    archive_target = output_dir / f"geyser-contracts-{value}.tar.gz"
    members = [ROOT / "schemas" / "VERSION", *sorted((ROOT / "schemas").rglob("*.json"))]
    with archive_target.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=epoch) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for source in members:
                    relative = source.relative_to(ROOT)
                    info = _tar_info(source, os.fspath(relative), epoch)
                    with source.open("rb") as handle:
                        archive.addfile(info, handle)


def payload_files(directory: Path) -> list[Path]:
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file()
        and path.name not in {"SHA256SUMS", "release-manifest.json"}
        and not path.name.endswith((".sigstore.json", ".intoto.jsonl"))
    )


def write_manifest(directory: Path, *, source_commit: str, tag: str, run_url: str) -> None:
    value = validate_source(tag)
    assets = [
        {"name": path.name, "sha256": sha256(path), "size": path.stat().st_size}
        for path in payload_files(directory)
    ]
    document: dict[str, Any] = {
        "schema_version": 1,
        "release": value,
        "tag": tag,
        "source_commit": source_commit,
        "workflow_run": run_url,
        "release_authorities": {
            "python": "PyPI Trusted Publishing",
            "manual_artifacts": "GitHub Releases",
            "cli": "geyserlabs/homebrew-tap",
        },
        "assets": assets,
    }
    (directory / "release-manifest.json").write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    checksummed = [*payload_files(directory), directory / "release-manifest.json"]
    (directory / "SHA256SUMS").write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in sorted(checksummed)),
        encoding="utf-8",
    )


def verify(directory: Path, tag: str) -> None:
    value = validate_source(tag)
    expected = {
        f"geyser_sdk-{value}-py3-none-any.whl",
        f"geyser_sdk-{value}.tar.gz",
        f"geyser_open-{value}-py3-none-any.whl",
        f"geyser_open-{value}.tar.gz",
        f"geyser-open-{value}-darwin-arm64.tar.gz",
        f"geyser-open-{value}-linux-amd64.tar.gz",
        f"geyser-openapi-{value}.json",
        f"geyser-contracts-{value}.tar.gz",
        *GENERATED,
    }
    missing = sorted(name for name in expected if not (directory / name).is_file())
    if missing:
        raise ValueError(f"release assets missing: {', '.join(missing)}")
    lines = (directory / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    for line in lines:
        expected_hash, name = line.split("  ", 1)
        path = directory / name
        if not path.is_file() or sha256(path) != expected_hash:
            raise ValueError(f"checksum mismatch: {name}")
    manifest = json.loads((directory / "release-manifest.json").read_text(encoding="utf-8"))
    if manifest["tag"] != tag or manifest["release"] != value:
        raise ValueError("release manifest identity mismatch")


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate-source")
    validate.add_argument("--tag")
    inventory = commands.add_parser("inventory")
    inventory.add_argument("--output", type=Path, required=True)
    inventory.add_argument("--source-commit", required=True)
    contracts = commands.add_parser("contracts")
    contracts.add_argument("--output-dir", type=Path, required=True)
    contracts.add_argument("--source-epoch", type=int, required=True)
    manifest = commands.add_parser("manifest")
    manifest.add_argument("--asset-dir", type=Path, required=True)
    manifest.add_argument("--source-commit", required=True)
    manifest.add_argument("--tag", required=True)
    manifest.add_argument("--run-url", required=True)
    verify_assets = commands.add_parser("verify")
    verify_assets.add_argument("--asset-dir", type=Path, required=True)
    verify_assets.add_argument("--tag", required=True)
    args = parser.parse_args()
    try:
        if args.command == "validate-source":
            print(validate_source(args.tag))
        elif args.command == "inventory":
            dependency_inventory(args.output, args.source_commit)
        elif args.command == "contracts":
            args.output_dir.mkdir(parents=True, exist_ok=True)
            contract_assets(args.output_dir, args.source_epoch)
        elif args.command == "manifest":
            write_manifest(
                args.asset_dir,
                source_commit=args.source_commit,
                tag=args.tag,
                run_url=args.run_url,
            )
        else:
            verify(args.asset_dir, args.tag)
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise SystemExit(f"release validation failed: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
