#!/usr/bin/env python3
"""Verify names, contents, dependencies, and runtime-monolith separation."""

from __future__ import annotations

import argparse
import zipfile
from email.parser import Parser
from pathlib import Path

FORBIDDEN = ("a2a_claude_agent", "anthropic", "openai", "playwright", "lancedb")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dist", type=Path)
    args = parser.parse_args()
    wheels = sorted(args.dist.glob("*.whl"))
    if len(wheels) != 2:
        raise SystemExit(f"expected exactly two wheels, found {len(wheels)}")
    names: set[str] = set()
    for wheel in wheels:
        with zipfile.ZipFile(wheel) as archive:
            metadata_name = next(name for name in archive.namelist() if name.endswith("METADATA"))
            metadata = Parser().parsestr(archive.read(metadata_name).decode())
            names.add(str(metadata["Name"]))
            content = "\n".join(archive.namelist()).casefold()
            if any(item in content for item in FORBIDDEN):
                raise SystemExit(f"private/runtime dependency leaked into {wheel.name}")
            if metadata["Name"] == "geyser-sdk":
                requirements = "\n".join(metadata.get_all("Requires-Dist", []))
                if any(item in requirements.casefold() for item in FORBIDDEN):
                    raise SystemExit("SDK has a forbidden runtime/provider dependency")
    if names != {"geyser-open", "geyser-sdk"}:
        raise SystemExit(f"unexpected distribution names: {sorted(names)}")
    print("verified distributions: geyser-sdk, geyser-open")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
