"""Command line entry point for the public Geyser developer platform."""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
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
    LocalEmulator,
    PackagePromotion,
    PackageUpload,
    ProblemError,
    TypedTask,
    bytes_digest,
    normalize_contract,
    validate_outcome,
)

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
    parser.add_argument("--api-url", default=os.getenv("GEYSER_API_URL", DEFAULT_API_URL))
    parser.add_argument("--profile", default=os.getenv("GEYSER_PROFILE", "default"))
    parser.add_argument("--json", action="store_true", help="emit stable JSON")
    parser.add_argument("--allow-file-credentials", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)

    login = commands.add_parser("login", help="authenticate with OAuth device flow")
    login.add_argument("--scope", action="append", dest="scopes")
    login.add_argument("--no-browser", action="store_true")
    login.add_argument("--service-token-stdin", action="store_true", help=argparse.SUPPRESS)
    commands.add_parser("logout", help="remove the current profile credential")
    commands.add_parser("doctor", help="check local configuration and public API reachability")

    init = commands.add_parser("init", help="create a safe extension scaffold")
    init.add_argument("kind", choices=KINDS)
    init.add_argument("name")
    init.add_argument("--output", type=Path, default=Path.cwd())
    for name in ("validate", "test", "dev", "package"):
        _add_path(commands.add_parser(name))
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
    promote.add_argument("--canary", action="store_true", required=True)
    promote.add_argument("--yes", action="store_true")
    commands.add_parser("status", help="list package lifecycle state")

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
    fork.add_argument("--child-run-id", required=True)
    fork.add_argument("--expected-sequence", type=int, required=True)
    fork.add_argument("--reason-code", default="developer_requested")
    fork.add_argument("--yes", action="store_true")
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
    decide.add_argument("--expected-sequence", type=int, required=True)
    decide.add_argument("--binding-digest", required=True)
    decide.add_argument("--reason-code", required=True)
    decide.add_argument("--yes", action="store_true")
    capabilities = commands.add_parser("capabilities")
    capabilities.add_argument("--agent", required=True)
    commands.add_parser("version")
    return parser


def _store(args: argparse.Namespace) -> CredentialStore:
    return CredentialStore(args.profile, allow_file_fallback=args.allow_file_credentials)


def _client(args: argparse.Namespace) -> GeyserClient:
    credential = _store(args).load()
    if credential is None:
        raise RuntimeError("not authenticated; run `geyser login`")
    return GeyserClient(args.api_url, credential.access_token)


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
            raise RuntimeError(f"frozen cases failed: {result['failed']}")
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
        result = test_extension(root)
        task = TypedTask(
            task_id="local-task",
            context_id="local-context",
            prompt_digest="sha256:" + "0" * 64,
            model_ref="deterministic:echo",
        )
        emulator = LocalEmulator()
        emulator.admit("local-run", task)
        emulator.append(
            "local-run",
            event_type="run.completed",
            key="complete",
            expected_sequence=1,
            data={
                "extension_digest": bytes_digest(
                    root.joinpath("geyser-package.json").read_bytes()
                )
            },
        )
        return {"extension": result, "run": emulator.project("local-run"), "network_used": False}
    raise RuntimeError("unknown local command")


def _doctor(args: argparse.Namespace) -> dict[str, Any]:
    credential = _store(args).load()
    reachable = False
    api_version = ""
    try:
        response = httpx.get(f"{args.api_url.rstrip('/')}/api/v1/openapi.json", timeout=5)
        reachable = response.status_code == 200
        if reachable:
            api_version = str(response.json().get("info", {}).get("version") or "")
    except httpx.HTTPError:
        pass
    return {
        "python": sys.version.split()[0],
        "cli_version": __version__,
        "api_url": args.api_url,
        "api_reachable": reachable,
        "api_version": api_version,
        "authenticated": credential is not None,
        "profile": args.profile,
    }


def _handle_network(args: argparse.Namespace) -> Any:
    with _client(args) as client:
        if args.command == "status":
            return client.list_packages()
        if args.command == "capabilities":
            return client.capabilities(agent_name=args.agent)
        if args.command == "runs":
            if args.runs_command == "list":
                return client.list_runs(customer=args.customer)
            if args.runs_command == "get":
                return client.get_run(args.run_id, customer=args.customer)
            if args.runs_command == "trace":
                return client.trace(args.run_id, customer=args.customer)
            if args.runs_command == "watch":
                return {"events": list(client.watch_events(args.run_id, customer=args.customer))}
            if args.runs_command == "stop":
                operation = {
                    "operation": "stop_run",
                    "run_id": args.run_id,
                    "expected_sequence": args.expected_sequence,
                }
                _confirm(args, operation)
                request = CancelRequest(
                    cancellation_id="cancel_" + uuid.uuid4().hex,
                    expected_sequence=args.expected_sequence,
                    reason_code=args.reason_code,
                )
                return client.cancel_run(args.run_id, request)
            operation = {
                "operation": "fork_run",
                "run_id": args.run_id,
                "child_run_id": args.child_run_id,
                "expected_sequence": args.expected_sequence,
            }
            _confirm(args, operation)
            fork_request = ForkCreate(
                fork_id="fork_" + uuid.uuid4().hex,
                child_run_id=args.child_run_id,
                expected_sequence=args.expected_sequence,
                reason_code=args.reason_code,
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
            return client.decide_approval(args.run_id, args.approval_id, decision)
        if args.command == "publish":
            archive = args.archive.expanduser().resolve()
            details = inspect_archive(archive)
            manifest = _manifest_from_archive(archive)
            _confirm(args, {"operation": "package_upload", "stage": "staging", **details})
            bundle = {}
            if args.signature_bundle:
                bundle = json.loads(args.signature_bundle.read_text(encoding="utf-8"))
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
            _confirm(args, {
                "operation": "package_promotion",
                "package_id": args.package_id,
                "target": "canary",
                "expected_digest": args.digest,
            })
            promotion = PackagePromotion(
                promotion_id="promote_" + uuid.uuid4().hex,
                target="canary",
                expected_digest=args.digest,
            )
            return client.promote_package(args.package_id, promotion)
    raise RuntimeError("unknown network command")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "version":
            value: Any = {"geyser_open": __version__}
        elif args.command == "login":
            store = _store(args)
            if args.service_token_stdin:
                value = login_service_token(store, sys.stdin.readline())
            else:
                def notify(device: DeviceAuthorization) -> None:
                    emit({
                        "verification_uri": device.verification_uri,
                        "user_code": device.user_code,
                    }, machine=args.json)

                value = login_device(
                    args.api_url,
                    store,
                    scopes=args.scopes or DEFAULT_SCOPES,
                    open_browser=not args.no_browser,
                    notify=notify,
                )
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
