#!/usr/bin/env python3
"""Finalize versioned GitHub Pages metadata after a Mike deployment."""

from __future__ import annotations

import argparse
import gzip
import re
import shutil
from pathlib import Path

VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:b[0-9]+)?$")
SITE_ROOT = "https://docs.geyserlabs.ai/"
LOCATION = re.compile(r"<loc>([^<]+)</loc>")


def _write_deterministic_gzip(path: Path, content: bytes) -> None:
    with path.open("wb") as destination:
        with gzip.GzipFile(filename="", mode="wb", fileobj=destination, mtime=0) as archive:
            archive.write(content)


def _version_sitemap(path: Path, version: str) -> bytes:
    content = path.read_text(encoding="utf-8")
    if "<!DOCTYPE" in content or "<!ENTITY" in content:
        raise ValueError("generated sitemap must not contain XML declarations with external data")
    locations = LOCATION.findall(content)
    if not locations:
        raise ValueError("generated sitemap does not contain any locations")
    version_root = f"{SITE_ROOT}{version}/"

    def rewrite(location: re.Match[str]) -> str:
        value = location.group(1)
        if not value.startswith(SITE_ROOT):
            raise ValueError(f"sitemap location is outside {SITE_ROOT}: {value}")
        if value.startswith(version_root):
            return location.group(0)
        return f"<loc>{version_root}{value.removeprefix(SITE_ROOT)}</loc>"

    return LOCATION.sub(rewrite, content).encode()


def finalize(pages_dir: Path, source_docs: Path, version: str) -> list[Path]:
    if not VERSION.fullmatch(version):
        raise ValueError("version must be an exact release such as 0.1.0")
    pages_dir = pages_dir.resolve()
    source_docs = source_docs.resolve()
    version_dir = pages_dir / version
    if not version_dir.is_dir():
        raise ValueError(f"published version directory is missing: {version_dir}")

    source_cname = source_docs / "CNAME"
    source_robots = source_docs / "robots.txt"
    source_llms = source_docs / "llms.txt"
    for source in (source_cname, source_robots, source_llms):
        if not source.is_file():
            raise ValueError(f"documentation metadata is missing: {source}")
    if source_cname.read_text(encoding="utf-8").strip() != "docs.geyserlabs.ai":
        raise ValueError("CNAME must bind the documented developer hostname")

    sitemap = version_dir / "sitemap.xml"
    if not sitemap.is_file():
        raise ValueError(f"published sitemap is missing: {sitemap}")
    sitemap_content = _version_sitemap(sitemap, version)

    outputs = [pages_dir / name for name in ("CNAME", "robots.txt", "llms.txt")]
    for source, destination in zip(
        (source_cname, source_robots, source_llms), outputs, strict=True
    ):
        shutil.copyfile(source, destination)

    sitemap.write_bytes(sitemap_content)
    version_gzip = version_dir / "sitemap.xml.gz"
    _write_deterministic_gzip(version_gzip, sitemap_content)
    root_sitemap = pages_dir / "sitemap.xml"
    root_sitemap.write_bytes(sitemap_content)
    root_gzip = pages_dir / "sitemap.xml.gz"
    _write_deterministic_gzip(root_gzip, sitemap_content)
    outputs.extend((sitemap, version_gzip, root_sitemap, root_gzip))
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages-dir", type=Path, required=True)
    parser.add_argument("--source-docs", type=Path, required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    try:
        outputs = finalize(args.pages_dir, args.source_docs, args.version)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"documentation finalization failed: {exc}") from exc
    print(f"finalized {len(outputs)} GitHub Pages metadata files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
