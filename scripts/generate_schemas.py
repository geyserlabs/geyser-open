#!/usr/bin/env python3
"""Generate deterministic public JSON Schemas and the semantic OpenAPI surface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from geyser_sdk.bundles import ModelSelection, TaskBundle
from geyser_sdk.models import (
    API_VERSION,
    ApprovalDecision,
    ApprovalPage,
    ApprovalResponse,
    CancelRequest,
    CapabilityResponse,
    EvaluationCreate,
    ForkCreate,
    ForkResponse,
    InputCreate,
    InputResponse,
    PackagePage,
    PackagePromotion,
    PackageResponse,
    PackageUpload,
    ReplayCreate,
    ResultResponse,
    RevocationResponse,
    RunEventPage,
    RunPage,
    RunResponse,
    TaskCreate,
    TaskPage,
    TaskResponse,
    TraceResponse,
)
from geyser_sdk.replay import ToolStubs
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / API_VERSION
OPENAPI_PATH = ROOT / "openapi" / "geyser-v1.openapi.json"
MODELS: dict[str, type[BaseModel]] = {
    model.__name__: model
    for model in (
        ModelSelection,
        TaskBundle,
        ToolStubs,
        ApprovalDecision,
        ApprovalPage,
        ApprovalResponse,
        CancelRequest,
        CapabilityResponse,
        EvaluationCreate,
        ForkCreate,
        ForkResponse,
        InputCreate,
        InputResponse,
        ResultResponse,
        RevocationResponse,
        PackagePage,
        PackagePromotion,
        PackageResponse,
        PackageUpload,
        ReplayCreate,
        RunEventPage,
        RunPage,
        RunResponse,
        TaskCreate,
        TaskPage,
        TaskResponse,
        TraceResponse,
    )
}


def encoded(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def openapi() -> dict[str, Any]:
    """The server-exported snapshot is the sole OpenAPI authority.

    fleet-coordinator/scripts/export-developer-openapi.py produces these exact
    bytes from real routes. This repository only derives SDK model schemas.
    """
    value: dict[str, Any] = json.loads(OPENAPI_PATH.read_text())
    if value.get("info", {}).get("version") != API_VERSION:
        raise ValueError("server OpenAPI version does not match the SDK")
    return value


def outputs() -> dict[Path, str]:
    values = {
        SCHEMA_DIR / f"{name}.schema.json": encoded(model.model_json_schema())
        for name, model in MODELS.items()
    }
    values[OPENAPI_PATH] = encoded(openapi())
    values[ROOT / "schemas" / "VERSION"] = API_VERSION + "\n"
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale: list[str] = []
    for path, content in outputs().items():
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    if stale:
        raise SystemExit("generated public contracts are stale: " + ", ".join(stale))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
