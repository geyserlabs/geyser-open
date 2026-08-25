"""Typed synchronous and asynchronous clients for Geyser Developer API v1."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator, Callable, Iterator
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from .errors import Problem, ProblemError, ResponseValidationError, TransportError
from .models import (
    TERMINAL_RUN_STATES,
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
    Run,
    RunEvent,
    RunEventPage,
    RunPage,
    RunResponse,
    Task,
    TaskCreate,
    TaskPage,
    TaskResponse,
    TraceResponse,
)

ModelT = TypeVar("ModelT", bound=BaseModel)
TokenProvider = Callable[[], str]
_RETRYABLE = frozenset({408, 429, 502, 503, 504})
_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def _token_provider(token: str | TokenProvider) -> TokenProvider:
    if callable(token):
        return token
    if not token.strip():
        raise ValueError("an explicit developer or customer access token is required")
    return lambda: token


def _headers(provider: TokenProvider, idempotency_key: str) -> dict[str, str]:
    token = provider().strip()
    if not token:
        raise ValueError("credential provider returned an empty token")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    return headers


def _decode(response: httpx.Response, model: type[ModelT]) -> ModelT:
    try:
        body = response.json()
    except ValueError as exc:
        raise ResponseValidationError("Geyser returned invalid JSON") from exc
    if response.status_code >= 400:
        if not isinstance(body, dict):
            body = {}
        raise ProblemError(Problem.from_mapping(body, response.status_code))
    try:
        return model.model_validate(body)
    except ValidationError as exc:
        raise ResponseValidationError(
            f"Geyser response failed {model.__name__} validation"
        ) from exc


def _retry_allowed(method: str, idempotency_key: str) -> bool:
    return method.upper() in _SAFE_METHODS or bool(idempotency_key)


class AsyncGeyserClient:
    """Reusable async client; call ``aclose`` or use it as a context manager."""

    def __init__(
        self,
        base_url: str,
        token: str | TokenProvider,
        *,
        timeout: float | httpx.Timeout = 30.0,
        max_retries: int = 2,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not base_url.startswith(("https://", "http://localhost", "http://127.0.0.1")):
            raise ValueError("base_url must use HTTPS except for loopback development")
        if max_retries < 0 or max_retries > 8:
            raise ValueError("max_retries must be between 0 and 8")
        self._token = _token_provider(token)
        self._max_retries = max_retries
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"), timeout=timeout, transport=transport
        )

    async def __aenter__(self) -> AsyncGeyserClient:
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        model: type[ModelT],
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        idempotency_key: str = "",
        if_match: int | None = None,
    ) -> ModelT:
        headers = _headers(self._token, idempotency_key)
        if if_match is not None:
            headers["If-Match"] = f'"run-v{if_match}"'
        can_retry = _retry_allowed(method, idempotency_key)
        attempts = self._max_retries + 1 if can_retry else 1
        response: httpx.Response | None = None
        for attempt in range(attempts):
            try:
                response = await self._client.request(
                    method, path, json=json, params=params, headers=headers
                )
            except httpx.TransportError as exc:
                if attempt + 1 >= attempts:
                    raise TransportError("Geyser could not be reached") from exc
            else:
                if response.status_code not in _RETRYABLE or attempt + 1 >= attempts:
                    return _decode(response, model)
            await asyncio.sleep(0.1 * (2**attempt))
        raise TransportError("Geyser could not be reached")

    async def create_task(self, task: TaskCreate, *, idempotency_key: str) -> TaskResponse:
        if not idempotency_key:
            raise ValueError("create_task requires an idempotency_key")
        return await self._request(
            "POST",
            "/api/v1/tasks",
            TaskResponse,
            json=task.model_dump(mode="json"),
            idempotency_key=idempotency_key,
        )

    async def get_task(self, task_id: str) -> TaskResponse:
        return await self._request("GET", f"/api/v1/tasks/{task_id}", TaskResponse)

    async def list_tasks(self, *, cursor: str = "", limit: int = 100) -> TaskPage:
        return await self._request(
            "GET", "/api/v1/tasks", TaskPage, params={"cursor": cursor, "limit": limit}
        )

    async def iter_tasks(self, *, limit: int = 100) -> AsyncIterator[Task]:
        cursor = ""
        while True:
            page = await self.list_tasks(cursor=cursor, limit=limit)
            for item in page.data:
                yield item
            if not page.next_cursor:
                return
            cursor = page.next_cursor

    async def capabilities(self, *, agent_name: str) -> CapabilityResponse:
        return await self._request(
            "GET", "/api/v1/capabilities", CapabilityResponse, params={"agent_name": agent_name}
        )

    async def get_run(self, run_id: str, *, customer: bool = False) -> RunResponse:
        prefix = "/api/v1/customer" if customer else "/api/v1"
        return await self._request("GET", f"{prefix}/runs/{run_id}", RunResponse)

    async def list_runs(
        self, *, cursor: str = "", limit: int = 100, customer: bool = False
    ) -> RunPage:
        prefix = "/api/v1/customer" if customer else "/api/v1"
        return await self._request(
            "GET", f"{prefix}/runs", RunPage, params={"cursor": cursor, "limit": limit}
        )

    async def iter_runs(
        self, *, limit: int = 100, customer: bool = False
    ) -> AsyncIterator[Run]:
        cursor = ""
        while True:
            page = await self.list_runs(cursor=cursor, limit=limit, customer=customer)
            for item in page.data:
                yield item
            if not page.next_cursor:
                return
            cursor = page.next_cursor

    async def events(
        self,
        run_id: str,
        *,
        after_sequence: int = 0,
        limit: int = 200,
        customer: bool = False,
    ) -> RunEventPage:
        prefix = "/api/v1/customer" if customer else "/api/v1"
        return await self._request(
            "GET",
            f"{prefix}/runs/{run_id}/events",
            RunEventPage,
            params={"cursor": after_sequence, "limit": limit},
        )

    async def watch_events(
        self,
        run_id: str,
        *,
        after_sequence: int = 0,
        poll_interval: float = 1.0,
        customer: bool = False,
    ) -> AsyncIterator[RunEvent]:
        sequence = after_sequence
        while True:
            page = await self.events(
                run_id, after_sequence=sequence, customer=customer
            )
            for event in page.data:
                sequence = max(sequence, event.sequence)
                yield event
            run = await self.get_run(run_id, customer=customer)
            if run.run.state in TERMINAL_RUN_STATES and sequence >= page.current_sequence:
                return
            await asyncio.sleep(max(0.05, poll_interval))

    async def trace(
        self, run_id: str, *, visibility: str = "customer", customer: bool = False
    ) -> TraceResponse:
        prefix = "/api/v1/customer" if customer else "/api/v1"
        return await self._request(
            "GET",
            f"{prefix}/runs/{run_id}/trace",
            TraceResponse,
            params={"visibility": visibility},
        )

    async def decide_approval(
        self, run_id: str, approval_id: str, decision: ApprovalDecision
    ) -> RunResponse:
        return await self._request(
            "POST",
            f"/api/v1/customer/runs/{run_id}/approvals/{approval_id}/decision",
            RunResponse,
            json=decision.model_dump(mode="json"),
            idempotency_key=decision.decision_id,
            if_match=decision.expected_approval_sequence,
        )

    async def list_approvals(
        self, *, cursor: str = "", limit: int = 100
    ) -> ApprovalPage:
        return await self._request(
            "GET",
            "/api/v1/customer/approvals",
            ApprovalPage,
            params={"cursor": cursor, "limit": limit},
        )

    async def get_approval(self, approval_id: str) -> ApprovalResponse:
        return await self._request(
            "GET", f"/api/v1/customer/approvals/{approval_id}", ApprovalResponse
        )

    async def upload_package(
        self, package: PackageUpload, *, idempotency_key: str
    ) -> PackageResponse:
        if not idempotency_key:
            raise ValueError("upload_package requires an idempotency_key")
        return await self._request(
            "POST",
            "/api/v1/packages",
            PackageResponse,
            json=package.model_dump(mode="json"),
            idempotency_key=idempotency_key,
        )

    async def promote_package(
        self, package_id: str, promotion: PackagePromotion
    ) -> PackageResponse:
        return await self._request(
            "POST",
            f"/api/v1/packages/{package_id}/promotions",
            PackageResponse,
            json=promotion.model_dump(mode="json"),
            idempotency_key=promotion.promotion_id,
        )

    async def list_packages(self, *, cursor: str = "", limit: int = 100) -> PackagePage:
        return await self._request(
            "GET", "/api/v1/packages", PackagePage, params={"cursor": cursor, "limit": limit}
        )

    async def cancel_run(self, run_id: str, request: CancelRequest) -> RunResponse:
        return await self._request(
            "POST",
            f"/api/v1/customer/runs/{run_id}/cancel",
            RunResponse,
            json=request.model_dump(mode="json"),
            idempotency_key=request.cancellation_id,
            if_match=request.expected_sequence,
        )

    async def evaluate(self, run_id: str, evaluation: EvaluationCreate) -> RunResponse:
        return await self._request(
            "POST",
            f"/api/v1/customer/runs/{run_id}/evaluations",
            RunResponse,
            json=evaluation.model_dump(mode="json"),
            idempotency_key=evaluation.evaluation_id,
            if_match=evaluation.expected_sequence,
        )

    async def fork(self, run_id: str, fork: ForkCreate) -> RunResponse:
        return await self._request(
            "POST",
            f"/api/v1/customer/runs/{run_id}/forks",
            RunResponse,
            json=fork.model_dump(mode="json"),
            idempotency_key=fork.fork_id,
            if_match=fork.expected_sequence,
        )


class GeyserClient:
    """Reusable synchronous client with the same semantic operations."""

    def __init__(
        self,
        base_url: str,
        token: str | TokenProvider,
        *,
        timeout: float | httpx.Timeout = 30.0,
        max_retries: int = 2,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not base_url.startswith(("https://", "http://localhost", "http://127.0.0.1")):
            raise ValueError("base_url must use HTTPS except for loopback development")
        if max_retries < 0 or max_retries > 8:
            raise ValueError("max_retries must be between 0 and 8")
        self._token = _token_provider(token)
        self._max_retries = max_retries
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"), timeout=timeout, transport=transport
        )

    def __enter__(self) -> GeyserClient:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def _request(
        self,
        method: str,
        path: str,
        model: type[ModelT],
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        idempotency_key: str = "",
        if_match: int | None = None,
    ) -> ModelT:
        headers = _headers(self._token, idempotency_key)
        if if_match is not None:
            headers["If-Match"] = f'"run-v{if_match}"'
        attempts = self._max_retries + 1 if _retry_allowed(method, idempotency_key) else 1
        for attempt in range(attempts):
            try:
                response = self._client.request(
                    method, path, json=json, params=params, headers=headers
                )
            except httpx.TransportError as exc:
                if attempt + 1 >= attempts:
                    raise TransportError("Geyser could not be reached") from exc
            else:
                if response.status_code not in _RETRYABLE or attempt + 1 >= attempts:
                    return _decode(response, model)
            time.sleep(0.1 * (2**attempt))
        raise TransportError("Geyser could not be reached")

    def create_task(self, task: TaskCreate, *, idempotency_key: str) -> TaskResponse:
        if not idempotency_key:
            raise ValueError("create_task requires an idempotency_key")
        return self._request(
            "POST",
            "/api/v1/tasks",
            TaskResponse,
            json=task.model_dump(mode="json"),
            idempotency_key=idempotency_key,
        )

    def get_task(self, task_id: str) -> TaskResponse:
        return self._request("GET", f"/api/v1/tasks/{task_id}", TaskResponse)

    def list_tasks(self, *, cursor: str = "", limit: int = 100) -> TaskPage:
        return self._request(
            "GET", "/api/v1/tasks", TaskPage, params={"cursor": cursor, "limit": limit}
        )

    def iter_tasks(self, *, limit: int = 100) -> Iterator[Task]:
        cursor = ""
        while True:
            page = self.list_tasks(cursor=cursor, limit=limit)
            yield from page.data
            if not page.next_cursor:
                return
            cursor = page.next_cursor

    def capabilities(self, *, agent_name: str) -> CapabilityResponse:
        return self._request(
            "GET", "/api/v1/capabilities", CapabilityResponse, params={"agent_name": agent_name}
        )

    def get_run(self, run_id: str, *, customer: bool = False) -> RunResponse:
        prefix = "/api/v1/customer" if customer else "/api/v1"
        return self._request("GET", f"{prefix}/runs/{run_id}", RunResponse)

    def list_runs(
        self, *, cursor: str = "", limit: int = 100, customer: bool = False
    ) -> RunPage:
        prefix = "/api/v1/customer" if customer else "/api/v1"
        return self._request(
            "GET", f"{prefix}/runs", RunPage, params={"cursor": cursor, "limit": limit}
        )

    def iter_runs(self, *, limit: int = 100, customer: bool = False) -> Iterator[Run]:
        cursor = ""
        while True:
            page = self.list_runs(cursor=cursor, limit=limit, customer=customer)
            yield from page.data
            if not page.next_cursor:
                return
            cursor = page.next_cursor

    def events(
        self,
        run_id: str,
        *,
        after_sequence: int = 0,
        limit: int = 200,
        customer: bool = False,
    ) -> RunEventPage:
        prefix = "/api/v1/customer" if customer else "/api/v1"
        return self._request(
            "GET",
            f"{prefix}/runs/{run_id}/events",
            RunEventPage,
            params={"cursor": after_sequence, "limit": limit},
        )

    def watch_events(
        self,
        run_id: str,
        *,
        after_sequence: int = 0,
        poll_interval: float = 1.0,
        customer: bool = False,
    ) -> Iterator[RunEvent]:
        sequence = after_sequence
        while True:
            page = self.events(run_id, after_sequence=sequence, customer=customer)
            for event in page.data:
                sequence = max(sequence, event.sequence)
                yield event
            run = self.get_run(run_id, customer=customer)
            if run.run.state in TERMINAL_RUN_STATES and sequence >= page.current_sequence:
                return
            time.sleep(max(0.05, poll_interval))

    def trace(
        self, run_id: str, *, visibility: str = "customer", customer: bool = False
    ) -> TraceResponse:
        prefix = "/api/v1/customer" if customer else "/api/v1"
        return self._request(
            "GET",
            f"{prefix}/runs/{run_id}/trace",
            TraceResponse,
            params={"visibility": visibility},
        )

    def decide_approval(
        self, run_id: str, approval_id: str, decision: ApprovalDecision
    ) -> RunResponse:
        return self._request(
            "POST",
            f"/api/v1/customer/runs/{run_id}/approvals/{approval_id}/decision",
            RunResponse,
            json=decision.model_dump(mode="json"),
            idempotency_key=decision.decision_id,
            if_match=decision.expected_approval_sequence,
        )

    def list_approvals(self, *, cursor: str = "", limit: int = 100) -> ApprovalPage:
        return self._request(
            "GET",
            "/api/v1/customer/approvals",
            ApprovalPage,
            params={"cursor": cursor, "limit": limit},
        )

    def get_approval(self, approval_id: str) -> ApprovalResponse:
        return self._request(
            "GET", f"/api/v1/customer/approvals/{approval_id}", ApprovalResponse
        )

    def upload_package(
        self, package: PackageUpload, *, idempotency_key: str
    ) -> PackageResponse:
        if not idempotency_key:
            raise ValueError("upload_package requires an idempotency_key")
        return self._request(
            "POST",
            "/api/v1/packages",
            PackageResponse,
            json=package.model_dump(mode="json"),
            idempotency_key=idempotency_key,
        )

    def promote_package(
        self, package_id: str, promotion: PackagePromotion
    ) -> PackageResponse:
        return self._request(
            "POST",
            f"/api/v1/packages/{package_id}/promotions",
            PackageResponse,
            json=promotion.model_dump(mode="json"),
            idempotency_key=promotion.promotion_id,
        )

    def list_packages(self, *, cursor: str = "", limit: int = 100) -> PackagePage:
        return self._request(
            "GET", "/api/v1/packages", PackagePage, params={"cursor": cursor, "limit": limit}
        )

    def cancel_run(self, run_id: str, request: CancelRequest) -> RunResponse:
        return self._request(
            "POST",
            f"/api/v1/customer/runs/{run_id}/cancel",
            RunResponse,
            json=request.model_dump(mode="json"),
            idempotency_key=request.cancellation_id,
            if_match=request.expected_sequence,
        )

    def evaluate(self, run_id: str, evaluation: EvaluationCreate) -> RunResponse:
        return self._request(
            "POST",
            f"/api/v1/customer/runs/{run_id}/evaluations",
            RunResponse,
            json=evaluation.model_dump(mode="json"),
            idempotency_key=evaluation.evaluation_id,
            if_match=evaluation.expected_sequence,
        )

    def fork(self, run_id: str, fork: ForkCreate) -> RunResponse:
        return self._request(
            "POST",
            f"/api/v1/customer/runs/{run_id}/forks",
            RunResponse,
            json=fork.model_dump(mode="json"),
            idempotency_key=fork.fork_id,
            if_match=fork.expected_sequence,
        )


__all__ = ["AsyncGeyserClient", "GeyserClient", "TokenProvider"]
