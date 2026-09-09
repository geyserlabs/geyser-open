"""Build the three maintained reference packages without publishing or signing."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from geyser_cli.extensions import package_extension

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    packages = []
    for name in ("issue-normalizer", "source-review-gate", "careful-review"):
        result = package_extension(ROOT / "examples/packages" / name)
        source = Path(result["path"])
        destination = args.output_dir / source.name
        if destination.exists():
            raise ValueError("Select an empty output directory for a new build.")
        shutil.copyfile(source, destination)
        packages.append({"name": name, "archive": destination.name, "digest": result["digest"]})
    (args.output_dir / "packages.json").write_text(json.dumps(packages, indent=2) + "\n")


if __name__ == "__main__":
    main()
