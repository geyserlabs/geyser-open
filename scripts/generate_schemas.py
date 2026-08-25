#!/usr/bin/env python3
"""Generate deterministic public JSON Schemas and the semantic OpenAPI surface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from geyser_sdk.models import (
    API_VERSION,
    ApprovalDecision,
    ApprovalPage,
    ApprovalResponse,
    CancelRequest,
    CapabilityResponse,
    EvaluationCreate,
    ForkCreate,
    PackagePage,
    PackagePromotion,
    PackageResponse,
    PackageUpload,
    RunEventPage,
    RunPage,
    RunResponse,
    TaskCreate,
    TaskPage,
    TaskResponse,
    TraceResponse,
)
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / API_VERSION
OPENAPI_PATH = ROOT / "openapi" / "geyser-v1.openapi.json"
MODELS: dict[str, type[BaseModel]] = {
    model.__name__: model
    for model in (
        ApprovalDecision,
        ApprovalPage,
        ApprovalResponse,
        CancelRequest,
        CapabilityResponse,
        EvaluationCreate,
        ForkCreate,
        PackagePage,
        PackagePromotion,
        PackageResponse,
        PackageUpload,
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
    ref = lambda name: {"$ref": f"#/components/schemas/{name}"}  # noqa: E731

    def response(name: str) -> dict[str, Any]:
        return {"200": {"description": "Success", "content": {
            "application/json": {"schema": ref(name)}
        }}}

    def operation(method: str, response_name: str, request_name: str = "") -> dict[str, Any]:
        value: dict[str, Any] = {
            "operationId": method,
            "security": [{"DeveloperBearer": []}],
            "responses": response(response_name),
        }
        if request_name:
            value["requestBody"] = {"required": True, "content": {
                "application/json": {"schema": ref(request_name)}
            }}
        return value

    return {
        "openapi": "3.1.0",
        "info": {"title": "Geyser Developer API", "version": API_VERSION},
        "servers": [{"url": "https://agents.geyserlabs.ai"}],
        "paths": {
            "/api/v1/tasks": {
                "get": operation("listTasks", "TaskPage"),
                "post": operation("createTask", "TaskResponse", "TaskCreate"),
            },
            "/api/v1/tasks/{task_id}": {"get": operation("getTask", "TaskResponse")},
            "/api/v1/capabilities": {"get": operation("getCapabilities", "CapabilityResponse")},
            "/api/v1/runs": {"get": operation("listRuns", "RunPage")},
            "/api/v1/runs/{run_id}": {"get": operation("getRun", "RunResponse")},
            "/api/v1/runs/{run_id}/events": {
                "get": operation("listRunEvents", "RunEventPage")
            },
            "/api/v1/runs/{run_id}/trace": {"get": operation("getRunTrace", "TraceResponse")},
            "/api/v1/customer/approvals": {"get": operation("listApprovals", "ApprovalPage")},
            "/api/v1/customer/approvals/{approval_id}": {
                "get": operation("getApproval", "ApprovalResponse")
            },
            "/api/v1/customer/runs/{run_id}/cancel": {
                "post": operation("cancelRun", "RunResponse", "CancelRequest")
            },
            "/api/v1/packages": {
                "get": operation("listPackages", "PackagePage"),
                "post": operation("uploadPackage", "PackageResponse", "PackageUpload"),
            },
            "/api/v1/packages/{package_id}/promotions": {
                "post": operation("promotePackage", "PackageResponse", "PackagePromotion")
            },
        },
        "components": {
            "securitySchemes": {"DeveloperBearer": {"type": "http", "scheme": "bearer"}},
            "schemas": {name: model.model_json_schema() for name, model in MODELS.items()},
        },
    }


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
