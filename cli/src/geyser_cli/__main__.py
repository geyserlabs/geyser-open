"""Command line entry point for the public Geyser developer platform."""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import httpx
from geyser_sdk import (
    ApprovalDecision,
    CancelRequest,
    ForkCreate,
    GeyserClient,
    InputCreate,
    PackagePromotion,
    PackageUpload,
    ProblemError,
    ReplayCreate,
    TaskCreate,
    normalize_contract,
    validate_outcome,
)
from geyser_sdk.extensions import run_extension
from geyser_sdk.urls import require_credential_destination, validate_api_url

from . import __version__
from .auth import DeviceAuthorization, login_device, login_service_token
from .credentials import CredentialStore
from .extensions import inspect_archive, package_extension, test_extension, validate_extension
from .output import emit
from .scaffolds import KINDS, scaffold

DEFAULT_API_URL = "https://agents.geyserlabs.ai"
DEFAULT_SCOPES = ["development:read", "runs:read", "packages:upload", "packages:stage"]


def _add_path(command: argparse.ArgumentParser) -> None:
    command.add_argument("path", nargs="?", type=Path, default=Path.cwd())


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="geyser", description="Build governed durable agents.")
    parser.add_argument("--api-url", default=os.getenv("GEYSER_API_URL"))
    parser.add_argument("--profile", default=os.getenv("GEYSER_PROFILE", "default"))
    parser.add_argument("--json", action="store_true", help="emit stable JSON")
    parser.add_argument("--allow-file-credentials", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)

    login = commands.add_parser("login", help="authenticate with OAuth device flow")
    login.add_argument("--scope", action="append", dest="scopes")
    login.add_argument("--no-browser", action="store_true")
    login.add_argument(
        "--service-token-stdin",
        action="store_true",
        help="read a service credential from stdin; supply its issued --api-url",
    )
    commands.add_parser("logout", help="remove the current profile credential")
    commands.add_parser("doctor", help="check local configuration and public API reachability")

    init = commands.add_parser("init", help="create a safe extension scaffold")
    init.add_argument("kind", choices=KINDS)
    init.add_argument("name")
    init.add_argument("--output", type=Path, default=Path.cwd())
    for name in ("validate", "test", "dev", "package"):
        local_command = commands.add_parser(name)
        _add_path(local_command)
        if name == "dev":
            local_command.add_argument("--input", type=Path)
    validate_result = commands.add_parser("validate-outcome")
    validate_result.add_argument("contract", type=Path)
    validate_result.add_argument("result", type=Path)
    sign = commands.add_parser("sign", help="sign exact package bytes using Sigstore")
    sign.add_argument("archive", type=Path)
    sign.add_argument("--bundle", type=Path)
    publish = commands.add_parser("publish", help="upload exact signed bytes to staging")
    publish.add_argument("archive", type=Path)
    publish.add_argument("--stage", action="store_true", required=True)
    publish.add_argument("--signature-bundle", type=Path)
    publish.add_argument("--yes", action="store_true")
    promote = commands.add_parser("promote", help="request promotion of exact staged bytes")
    promote.add_argument("package_id")
    promote.add_argument("--digest", required=True)
    target = promote.add_mutually_exclusive_group(required=True)
    target.add_argument("--canary", action="store_true")
    target.add_argument("--production", action="store_true")
    promote.add_argument("--yes", action="store_true")
    commands.add_parser("status", help="list package lifecycle state")

    revoke = commands.add_parser("revoke", help="revoke one exact package assignment")
    revoke.add_argument("package_id")
    revoke.add_argument("--digest", required=True)
    revoke.add_argument("--yes", action="store_true")
    tasks = commands.add_parser("tasks")
    task_commands = tasks.add_subparsers(dest="tasks_command", required=True)
    task_commands.add_parser("list")
    for action in ("get", "result", "wait"):
        command = task_commands.add_parser(action)
        command.add_argument("task_id")
        if action == "wait":
            command.add_argument("--timeout", type=float, default=300)
    create = task_commands.add_parser(
        "create", help="upload JSON and submit one idempotent bounded task"
    )
    create.add_argument("--input", type=Path, required=True)
    create.add_argument("--contract", type=Path)
    create.add_argument("--package", dest="package_id")
    create.add_argument("--require-write-approval", action="store_true")
    create.add_argument("--bundle", dest="bundle_package_id", default="")
    create.add_argument("--skill", dest="skill_package_ids", action="append", default=[])
    create.add_argument("--model-profile", dest="model_profile_package_id", default="")
    create.add_argument("--idempotency-key", required=True)
    create.add_argument("--max-cost", type=float, default=1.0)
    create.add_argument("--max-seconds", type=float, default=300)
    create.add_argument("--max-provider-requests", type=int, default=10)
    create.add_argument("--max-tool-calls", type=int, default=20)

    runs = commands.add_parser("runs")
    run_commands = runs.add_subparsers(dest="runs_command", required=True)
    run_list = run_commands.add_parser("list")
    run_list.add_argument("--customer", action="store_true")
    for name in ("get", "watch", "trace"):
        command = run_commands.add_parser(name)
        command.add_argument("run_id")
        command.add_argument("--customer", action="store_true")
    fork = run_commands.add_parser("fork")
    fork.add_argument("run_id")
    fork.add_argument(
        "--mode", choices=["model_only", "tool_stubbed", "read_only_shadow"], default="tool_stubbed"
    )
    fork.add_argument("--expected-sequence", type=int, required=True)
    fork.add_argument("--reason-code", default="developer_requested")
    fork.add_argument("--yes", action="store_true")
    replay = run_commands.add_parser("replay", help="create a new task from an original run input")
    replay.add_argument("run_id")
    replay.add_argument(
        "--mode",
        choices=["model_only", "tool_stubbed", "read_only_shadow", "full_reexecution"],
        required=True,
    )
    replay.add_argument("--expected-sequence", type=int, required=True)
    replay.add_argument("--idempotency-key", required=True)
    replay.add_argument("--stubs-ref", default="")
    replay.add_argument("--authority-ref", default="")
    replay.add_argument("--max-seconds", type=float, default=300)
    replay.add_argument("--max-cost", type=float, default=1.0)
    replay.add_argument("--yes", action="store_true")
    stop = run_commands.add_parser("stop")
    stop.add_argument("run_id")
    stop.add_argument("--expected-sequence", type=int, required=True)
    stop.add_argument("--reason-code", default="developer_requested")
    stop.add_argument("--yes", action="store_true")

    approvals = commands.add_parser("approvals")
    approval_commands = approvals.add_subparsers(dest="approvals_command", required=True)
    approval_commands.add_parser("list")
    approval_get = approval_commands.add_parser("get")
    approval_get.add_argument("approval_id")
    decide = approval_commands.add_parser("decide")
    decide.add_argument("run_id")
    decide.add_argument("approval_id")
    decide.add_argument("decision", choices=("approve", "reject"))
    decide.add_argument(
        "--expected-sequence", "--expected-approval-sequence", type=int, required=True
    )
    decide.add_argument("--expected-run-sequence", type=int, required=True)
    decide.add_argument("--binding-digest", required=True)
    decide.add_argument("--reason-code", required=True)
    decide.add_argument("--yes", action="store_true")
    capabilities = commands.add_parser("capabilities")
    capabilities.add_argument(
        "--agent", default="", help="optionally assert the project's assigned Agent name"
    )
    commands.add_parser("version")
    return parser


def _store(args: argparse.Namespace) -> CredentialStore:
    return CredentialStore(args.profile, allow_file_fallback=args.allow_file_credentials)


def _client(args: argparse.Namespace) -> GeyserClient:
    credential = _store(args).load()
    if credential is None:
        raise RuntimeError("not authenticated; run `geyser login`")
    destination = require_credential_destination(
        credential.api_url, args.api_url or credential.api_url
    )
    return GeyserClient(destination, credential.access_token)


def _confirm(args: argparse.Namespace, preview: dict[str, Any]) -> None:
    emit({"preview": preview, "server_authority_required": True}, machine=args.json)
    if args.yes:
        return
    if not sys.stdin.isatty() or input("Continue? [y/N] ").strip().casefold() not in {"y", "yes"}:
        raise RuntimeError("operation canceled before server authorization")


def _manifest_from_archive(path: Path) -> dict[str, Any]:
    import zipfile

    with zipfile.ZipFile(path) as archive:
        return cast(dict[str, Any], json.loads(archive.read("geyser-package.json")))


def _handle_local(args: argparse.Namespace) -> Any:
    if args.command == "init":
        return {"path": os.fspath(scaffold(args.kind, args.name, args.output)), "created": True}
    if args.command == "validate":
        return {"valid": True, **validate_extension(args.path)}
    if args.command == "test":
        result = test_extension(args.path)
        if result["failed"]:
            raise RuntimeError(f"frozen cases failed: {result['failures']}")
        return result
    if args.command == "package":
        return package_extension(args.path)
    if args.command == "validate-outcome":
        contract = normalize_contract(json.loads(args.contract.read_text(encoding="utf-8")))
        if contract is None:
            raise ValueError("outcome contract is empty")
        validate_outcome(contract, json.loads(args.result.read_text(encoding="utf-8")))
        return {"valid": True, "contract_digest": contract["contract_digest"]}
    if args.command == "dev":
        root = args.path.expanduser().resolve()
        validate_extension(root)
        value = (
            json.loads(args.input.read_text())
            if args.input
            else json.loads((root / "evals/cases.json").read_text())["cases"][0]["input"]
        )
        return {"result": run_extension(root, value), "sandboxed": True}
    raise RuntimeError("unknown local command")


def _doctor(args: argparse.Namespace) -> dict[str, Any]:
    credential = _store(args).load()
    destination = validate_api_url(
        args.api_url or (credential.api_url if credential else "") or DEFAULT_API_URL
    )
    reachable = False
    api_version = ""
    try:
        response = httpx.get(f"{destination}/api/v1/openapi.json", timeout=5)
        reachable = response.status_code == 200
        if reachable:
            api_version = str(response.json().get("info", {}).get("version") or "")
    except httpx.HTTPError:
        pass
    return {
        "python": sys.version.split()[0],
        "cli_version": __version__,
        "api_url": destination,
        "api_reachable": reachable,
        "api_version": api_version,
        "authenticated": credential is not None,
        "profile": args.profile,
    }


def _handle_network(args: argparse.Namespace) -> Any:
    if args.command == "tasks" and args.tasks_command == "create":
        if args.package_id and (
            args.bundle_package_id
            or args.skill_package_ids
            or args.model_profile_package_id
            or args.require_write_approval
        ):
            raise ValueError(
                "pure JSON handler tasks cannot select Agent instruction packages "
                "or write approvals"
            )
        TaskCreate.valid_budget(
            {
                "max_cost_usd": args.max_cost,
                "max_elapsed_seconds": args.max_seconds,
                "max_provider_requests": args.max_provider_requests,
                "max_tool_calls": args.max_tool_calls,
            }
        )
    with _client(args) as client:
        if args.command == "tasks":
            if args.tasks_command == "list":
                return client.list_tasks()
            if args.tasks_command == "get":
                return client.get_task(args.task_id)
            if args.tasks_command == "result":
                return client.result(args.task_id)
            if args.tasks_command == "wait":
                if not 0 < args.timeout <= 3600:
                    raise ValueError("wait timeout must be between 0 and 3600 seconds")
                deadline = time.monotonic() + args.timeout
                while True:
                    task = client.get_task(args.task_id).task
                    if task.state in {"completed", "failed", "canceled"}:
                        return {
                            "task": task.model_dump(),
                            "result": client.result(task.id).result.model_dump()
                            if task.state == "completed"
                            else None,
                        }
                    if time.monotonic() >= deadline:
                        raise RuntimeError("wait timed out; task continues remotely")
                    time.sleep(min(5, max(0, deadline - time.monotonic())))
            value = client.upload_input(InputCreate(value=json.loads(args.input.read_text())))
            outcome_ref = ""
            if args.contract:
                outcome_ref = client.upload_input(
                    InputCreate(
                        kind="outcome_contract", value=json.loads(args.contract.read_text())
                    )
                ).input.ref
            return client.create_task(
                TaskCreate(
                    input_ref=value.input.ref,
                    input_digest=value.input.digest,
                    require_write_approval=args.require_write_approval,
                    bundle_package_id=args.bundle_package_id,
                    skill_package_ids=args.skill_package_ids,
                    model_profile_package_id=args.model_profile_package_id,
                    outcome_contract_ref=outcome_ref,
                    budget={
                        "max_cost_usd": args.max_cost,
                        "max_elapsed_seconds": args.max_seconds,
                        "max_provider_requests": args.max_provider_requests,
                        "max_tool_calls": args.max_tool_calls,
                    },
                    metadata={"execution": "extension", "package_id": args.package_id}
                    if args.package_id
                    else {"execution": "agent"},
                ),
                idempotency_key=args.idempotency_key,
            )
        if args.command == "revoke":
            _confirm(
                args,
                {
                    "operation": "revoke_package",
                    "package_id": args.package_id,
                    "digest": args.digest,
                },
            )
            return client.revoke_package(args.package_id, expected_digest=args.digest)
        if args.command == "status":
            return client.list_packages()
        if args.command == "capabilities":
            return client.capabilities(agent_name=args.agent)
        if args.command == "runs":
            if args.runs_command == "replay":
                replay_request = ReplayCreate(
                    fork_key=args.idempotency_key,
                    expected_sequence=args.expected_sequence,
                    mode=args.mode,
                    stubs_ref=args.stubs_ref,
                    authority_ref=args.authority_ref,
                    budget={"max_cost_usd": args.max_cost, "max_elapsed_seconds": args.max_seconds},
                )
                _confirm(
                    args,
                    {
                        "operation": "replay_run",
                        "run_id": args.run_id,
                        "mode": args.mode,
                        "budget": replay_request.budget,
                    },
                )
                return client.replay(args.run_id, replay_request)
            if args.runs_command == "list":
                return client.list_runs(customer=args.customer)
            if args.runs_command == "get":
                return client.get_run(args.run_id, customer=args.customer)
            if args.runs_command == "trace":
                return client.trace(args.run_id, customer=args.customer)
            if args.runs_command == "stop":
                operation = {
                    "operation": "stop_run",
                    "run_id": args.run_id,
                    "expected_sequence": args.expected_sequence,
                }
                _confirm(args, operation)
                request = CancelRequest(
                    cancellation_id="can_" + uuid.uuid4().hex,
                    expected_sequence=args.expected_sequence,
                    reason_code=args.reason_code,
                )
                return client.cancel_run(args.run_id, request)
            operation = {
                "operation": "fork_run",
                "run_id": args.run_id,
                "mode": args.mode,
                "expected_sequence": args.expected_sequence,
            }
            _confirm(args, operation)
            fork_request = ForkCreate(
                fork_key="fork_" + uuid.uuid4().hex,
                mode=args.mode,
                expected_sequence=args.expected_sequence,
            )
            return client.fork(args.run_id, fork_request)
        if args.command == "approvals":
            if args.approvals_command == "list":
                return client.list_approvals()
            if args.approvals_command == "get":
                return client.get_approval(args.approval_id)
            operation = {
                "operation": "approval_decision",
                "run_id": args.run_id,
                "approval_id": args.approval_id,
                "decision": args.decision,
                "binding_digest": args.binding_digest,
            }
            _confirm(args, operation)
            decision = ApprovalDecision(
                decision_id="decision_" + uuid.uuid4().hex,
                decision=args.decision,
                expected_approval_sequence=args.expected_sequence,
                binding_digest=args.binding_digest,
                reason_code=args.reason_code,
            )
            return client.decide_approval(
                args.run_id,
                args.approval_id,
                decision,
                expected_run_sequence=args.expected_run_sequence,
            )
        if args.command == "publish":
            archive = args.archive.expanduser().resolve()
            details = inspect_archive(archive)
            manifest = _manifest_from_archive(archive)
            _confirm(args, {"operation": "package_upload", "stage": "staging", **details})
            bundle_path = args.signature_bundle or archive.with_suffix(
                archive.suffix + ".sigstore.json"
            )
            if not bundle_path.is_file():
                raise ValueError("sign the exact archive first or supply --signature-bundle")
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
            upload = PackageUpload(
                name=str(manifest["name"]),
                version=str(manifest["version"]),
                digest=str(details["digest"]),
                media_type="application/vnd.geyser.extension+zip",
                content_base64=base64.b64encode(archive.read_bytes()).decode(),
                signature_bundle=bundle,
            )
            return client.upload_package(upload, idempotency_key=str(details["digest"]))
        if args.command == "promote":
            _confirm(
                args,
                {
                    "operation": "package_promotion",
                    "package_id": args.package_id,
                    "target": "production" if args.production else "canary",
                    "expected_digest": args.digest,
                },
            )
            promotion = PackagePromotion(
                promotion_id="promote_" + uuid.uuid4().hex,
                target="production" if args.production else "canary",
                expected_digest=args.digest,
            )
            return client.promote_package(args.package_id, promotion)
    raise RuntimeError("unknown network command")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "login":
        args.api_url = args.api_url or DEFAULT_API_URL
    try:
        if args.command == "version":
            value: Any = {"geyser_open": __version__}
        elif args.command == "login":
            store = _store(args)
            if args.service_token_stdin:
                value = login_service_token(store, sys.stdin.readline(), api_url=args.api_url)
            else:

                def notify(device: DeviceAuthorization) -> None:
                    emit(
                        {
                            "verification_uri": device.verification_uri,
                            "user_code": device.user_code,
                        },
                        machine=args.json,
                    )

                value = login_device(
                    args.api_url,
                    store,
                    scopes=args.scopes or DEFAULT_SCOPES,
                    open_browser=not args.no_browser,
                    notify=notify,
                )
        elif args.command == "runs" and args.runs_command == "watch":
            with _client(args) as client:
                for event in client.watch_events(args.run_id, customer=args.customer):
                    emit(event, machine=args.json)
            return 0
        elif args.command == "logout":
            value = {"removed": _store(args).delete(), "profile": args.profile}
        elif args.command == "doctor":
            value = _doctor(args)
        elif args.command in {"init", "validate", "validate-outcome", "test", "dev", "package"}:
            value = _handle_local(args)
        elif args.command == "sign":
            archive = args.archive.expanduser().resolve()
            inspect_archive(archive)
            bundle = (
                args.bundle or archive.with_suffix(archive.suffix + ".sigstore.json")
            ).resolve()
            executable = shutil.which("sigstore")
            if executable is None:
                raise RuntimeError("Sigstore CLI is not installed")
            result = subprocess.run(  # noqa: S603 - resolved executable and argv, no shell
                [executable, "sign", "--bundle", os.fspath(bundle), os.fspath(archive)],
                check=False,
            )
            if result.returncode:
                raise RuntimeError("Sigstore signing failed; no package lifecycle state changed")
            value = {"signed": True, "archive": os.fspath(archive), "bundle": os.fspath(bundle)}
        else:
            value = _handle_network(args)
        emit(value, machine=args.json)
        return 0
    except (OSError, ValueError, RuntimeError, ProblemError, httpx.HTTPError) as exc:
        if args.json:
            emit({"error": type(exc).__name__, "detail": str(exc)}, machine=True)
        else:
            print(f"geyser: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
