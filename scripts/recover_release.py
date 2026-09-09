#!/usr/bin/env python3
"""Recover publication from a verified release build; never rebuild or retag."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
import urllib.error
import urllib.request
import zipfile
from email.parser import BytesParser
from pathlib import Path

REPO = "geyserlabs/geyser-open"


def release_version() -> str:
    tag = os.environ["RELEASE_TAG"]
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise ValueError("release tag must be an exact version")
    return tag[1:]


def api(path: str) -> dict:
    # Only fixed API paths and a validated numeric run ID reach this argv.
    return json.loads(subprocess.check_output(  # noqa: S603
        ["gh", "api", f"repos/{REPO}/{path}"]))  # noqa: S607


def verify_source() -> None:
    version = release_version()
    recovery_ref = os.environ.get("GITHUB_REF", "")
    if recovery_ref and not re.fullmatch(
            rf"refs/tags/v{re.escape(version)}-publish-[0-9]+", recovery_ref):
        raise ValueError("publication recovery requires an immutable publication tag")
    run_id = os.environ["REUSE_RUN_ID"]
    if not re.fullmatch(r"[0-9]+", run_id):
        raise ValueError("original release run must be a numeric ID")
    run = api(f"actions/runs/{run_id}")
    workflow = api("actions/workflows/release.yml")
    commit = subprocess.check_output(  # noqa: S603
        ["git", "rev-parse", f"refs/tags/v{version}^{{commit}}"], text=True,  # noqa: S607
    ).strip()
    if (run["head_sha"] != commit or run["workflow_id"] != workflow["id"]
            or run["repository"]["full_name"] != REPO
            or run["event"] not in {"push", "workflow_dispatch"}):
        raise ValueError("original build does not belong to this exact release source")
    jobs = api(f"actions/runs/{run_id}/jobs?per_page=100")["jobs"]
    required = {
        "python-distributions", "assemble",
        "standalone-cli (macos-14, darwin-arm64)",
        "standalone-cli (ubuntu-24.04, linux-amd64)",
    }
    passed = {job["name"] for job in jobs if job["conclusion"] == "success"}
    if not required <= passed:
        raise ValueError("original release build did not complete all required artifacts")
    print("Verified original build against the immutable release tag")


def verify_assets(root: Path, version: str) -> None:
    expected = {
        f"geyser-{name}-{version}.tar.gz" for name in ("contracts",)
    } | {
        f"geyser-open-{version}-{platform}.tar.gz"
        for platform in ("darwin-arm64", "linux-amd64")
    } | {f"geyser-openapi-{version}.json"} | {
        f"{name}-{version}{suffix}"
        for name in ("geyser_sdk", "geyser_open")
        for suffix in (".tar.gz", "-py3-none-any.whl")
    }
    if {path.name for path in root.iterdir()} != expected | {"SHA256SUMS"}:
        raise ValueError("release artifact inventory differs from the exact version")
    checksums = {}
    for line in (root / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split(None, 1)
        if name in checksums or name not in expected or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("invalid or duplicate artifact checksum")
        checksums[name] = digest
    if set(checksums) != expected:
        raise ValueError("artifact checksums are incomplete")
    for name, digest in checksums.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise ValueError("artifact checksum mismatch")
    for name in ("geyser_sdk", "geyser_open"):
        wheel = root / f"{name}-{version}-py3-none-any.whl"
        with zipfile.ZipFile(wheel) as archive:
            metadata = [p for p in archive.namelist() if p.endswith(".dist-info/METADATA")]
            if len(metadata) != 1:
                raise ValueError("wheel metadata is ambiguous")
            wheel_info = BytesParser().parsebytes(archive.read(metadata[0]))
        with tarfile.open(root / f"{name}-{version}.tar.gz") as archive:
            member = archive.getmember(f"{name}-{version}/PKG-INFO")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("sdist metadata is missing")
            sdist_info = BytesParser().parsebytes(stream.read())
        for info in (wheel_info, sdist_info):
            if info["Name"] != name.replace("_", "-") or info["Version"] != version:
                raise ValueError("distribution name or version differs from the release")
    print("Verified all checksums and wheel/sdist versions")


def already_published(root: Path, name: str, version: str) -> bool:
    if name not in {"geyser-sdk", "geyser-open"} or not re.fullmatch(
            r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("expected one exact Geyser distribution version")
    prefix = name.replace("-", "_")
    names = {f"{prefix}-{version}.tar.gz", f"{prefix}-{version}-py3-none-any.whl"}
    if {path.name for path in root.iterdir()} != names:
        raise ValueError("publication directory has an unexpected file inventory")
    expected = {filename: hashlib.sha256((root / filename).read_bytes()).hexdigest()
                for filename in names}
    try:
        # The host and project names are fixed; no metadata URL is followed.
        with urllib.request.urlopen(
                f"https://pypi.org/pypi/{name}/{version}/json", timeout=20) as response:
            value = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False
        raise
    rows = value["urls"]
    actual = {row["filename"]: row["digests"]["sha256"] for row in rows}
    if len(rows) != len(names) or actual != expected:
        raise ValueError("published distributions differ from the verified artifacts")
    if value["info"]["name"] != name or value["info"]["version"] != version:
        raise ValueError("published distribution identity differs from the release")
    return True


if __name__ == "__main__":
    if sys.argv[1] == "source":
        verify_source()
    elif sys.argv[1] == "assets":
        verify_assets(Path(sys.argv[2]), release_version())
    elif sys.argv[1] == "published":
        matched = already_published(Path(sys.argv[3]), sys.argv[2], release_version())
        with Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
            output.write(f"already_published={str(matched).lower()}\n")
        print("Existing publication matches" if matched else "Version is not yet published")
    else:
        raise SystemExit("expected source, assets or published")
