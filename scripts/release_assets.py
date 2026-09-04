#!/usr/bin/env python3
"""Build the public API contract assets included in a release."""

from __future__ import annotations

import argparse
import gzip
import os
import tarfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILES = (
    ROOT / "sdk" / "python" / "pyproject.toml",
    ROOT / "cli" / "pyproject.toml",
)


def version() -> str:
    values = {
        str(tomllib.loads(path.read_text(encoding="utf-8"))["project"]["version"])
        for path in VERSION_FILES
    }
    if len(values) != 1:
        raise ValueError(f"SDK and CLI versions differ: {sorted(values)}")
    return values.pop()


def _tar_info(path: Path, name: str, epoch: int) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name)
    info.size = path.stat().st_size
    info.mode = 0o644
    info.mtime = epoch
    info.uid = info.gid = 0
    info.uname = info.gname = "root"
    return info


def contract_assets(output_dir: Path, epoch: int) -> None:
    release = version()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"geyser-openapi-{release}.json").write_bytes(
        (ROOT / "openapi" / "geyser-v1.openapi.json").read_bytes()
    )
    archive_target = output_dir / f"geyser-contracts-{release}.tar.gz"
    members = [ROOT / "schemas" / "VERSION", *sorted((ROOT / "schemas").rglob("*.json"))]
    with archive_target.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=epoch) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for source in members:
                    relative = source.relative_to(ROOT)
                    info = _tar_info(source, os.fspath(relative), epoch)
                    with source.open("rb") as handle:
                        archive.addfile(info, handle)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("version", "contracts"))
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--source-epoch", type=int, default=0)
    args = parser.parse_args()
    try:
        if args.command == "version":
            print(version())
        else:
            if args.output_dir is None:
                parser.error("contracts requires --output-dir")
            contract_assets(args.output_dir, args.source_epoch)
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise SystemExit(f"release asset build failed: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
