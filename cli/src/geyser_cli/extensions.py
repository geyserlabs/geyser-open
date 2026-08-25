"""Validation, deterministic packaging, and frozen extension tests."""

from __future__ import annotations

import json
import os
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from geyser_sdk import bytes_digest
from pydantic import BaseModel, ConfigDict, Field

from .scaffolds import KINDS

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_PACKAGE_BYTES = 10 * 1024 * 1024
IGNORED_PARTS = frozenset({".git", ".geyser", ".venv", "__pycache__"})


class ExtensionManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    kind: str
    name: str
    version: str
    permissions: list[str] = Field(default_factory=list, max_length=128)


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON file {path}: {exc}") from exc


def validate_extension(root: Path) -> dict[str, Any]:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"extension directory does not exist: {root}")
    manifest_path = root / "geyser-package.json"
    manifest = ExtensionManifest.model_validate(_load_json(manifest_path))
    if manifest.schema_version != 1 or manifest.kind not in KINDS:
        raise ValueError("unsupported extension manifest kind or schema version")
    files = 0
    total = 0
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if set(relative.parts) & IGNORED_PARTS:
            continue
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise ValueError(f"extension contains unsafe file type: {relative}")
        if path.is_file():
            size = path.stat().st_size
            if size > MAX_FILE_BYTES:
                raise ValueError(f"extension file exceeds 2 MiB: {relative}")
            files += 1
            total += size
    if total > MAX_PACKAGE_BYTES:
        raise ValueError("extension exceeds the 10 MiB unpacked bound")
    cases_path = root / "evals" / "cases.json"
    cases = _load_json(cases_path)
    if not isinstance(cases, dict) or cases.get("frozen") is not True:
        raise ValueError("evals/cases.json must declare frozen=true")
    rows = cases.get("cases")
    if not isinstance(rows, list) or not rows:
        raise ValueError("evals/cases.json must contain at least one case")
    if not any(isinstance(row, dict) and row.get("critical") is True for row in rows):
        raise ValueError("at least one frozen critical denial case is required")
    return {"manifest": manifest.model_dump(), "files": files, "size_bytes": total}


def test_extension(root: Path) -> dict[str, Any]:
    validation = validate_extension(root)
    cases = _load_json(root.expanduser().resolve() / "evals" / "cases.json")["cases"]
    failed = [row.get("case_id", "unknown") for row in cases if row.get("expected") not in {
        "success", "deny_without_explicit_authority"
    }]
    return {
        **validation,
        "cases": len(cases),
        "passed": len(cases) - len(failed),
        "failed": failed,
    }


def package_extension(root: Path, output: Path | None = None) -> dict[str, Any]:
    root = root.expanduser().resolve()
    validation = validate_extension(root)
    manifest = validation["manifest"]
    output = output or root / ".geyser" / "dist" / (
        f"{manifest['name']}-{manifest['version']}.geyser.zip"
    )
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root)
            if not path.is_file() or set(relative.parts) & IGNORED_PARTS:
                continue
            info = zipfile.ZipInfo(PurePosixPath(relative).as_posix(), (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, path.read_bytes())
    package_bytes = output.read_bytes()
    if len(package_bytes) > MAX_PACKAGE_BYTES:
        output.unlink(missing_ok=True)
        raise ValueError("extension archive exceeds 10 MiB")
    return {
        "path": os.fspath(output),
        "name": manifest["name"],
        "version": manifest["version"],
        "digest": bytes_digest(package_bytes),
        "size_bytes": len(package_bytes),
        "media_type": "application/vnd.geyser.extension+zip",
    }


def inspect_archive(path: Path) -> dict[str, Any]:
    path = path.expanduser().resolve()
    if path.stat().st_size > MAX_PACKAGE_BYTES:
        raise ValueError("archive exceeds 10 MiB")
    total = 0
    names: set[str] = set()
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            pure = PurePosixPath(info.filename)
            if pure.is_absolute() or ".." in pure.parts or "" in pure.parts:
                raise ValueError("archive contains path traversal")
            if info.filename in names:
                raise ValueError("archive contains duplicate paths")
            names.add(info.filename)
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError("archive contains a symbolic link")
            total += info.file_size
            if info.file_size > MAX_FILE_BYTES or total > MAX_PACKAGE_BYTES:
                raise ValueError("archive exceeds unpacked safety bounds")
    return {"path": os.fspath(path), "digest": bytes_digest(path.read_bytes()), "files": len(names)}


__all__ = [
    "ExtensionManifest",
    "inspect_archive",
    "package_extension",
    "test_extension",
    "validate_extension",
]
