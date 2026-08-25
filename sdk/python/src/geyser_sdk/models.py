from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

API_VERSION = "2026-08-24"
CapabilityMode = Literal["native", "geyser_emulated", "unsupported", "forbidden"]
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_REFERENCE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:[^\s]{1,1000}$")


class PublicModel(BaseModel):
    # Public v1 is additive. Known fields are typed while future fields survive
    # round-trips instead of breaking an older supported SDK minor.
    model_config = ConfigDict(extra="allow", frozen=True)


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TaskCreate(StrictInput):
    input_ref: str
    input_digest: str
    required_capabilities: list[str] = Field(default_factory=list, max_length=64)
    outcome_contract_ref: str = Field(default="", max_length=1000)
    budget: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("input_ref")
    @classmethod
    def reference_is_opaque(cls, value: str) -> str:
        if _REFERENCE.fullmatch(value) is None:
            raise ValueError("input_ref must be an opaque reference")
        return value

    @field_validator("input_digest")
    @classmethod
    def digest_is_exact(cls, value: str) -> str:
        if _DIGEST.fullmatch(value) is None:
            raise ValueError("input_digest must be sha256:<64 lowercase hex>")
        return value


class Task(PublicModel):
    id: str
    project_id: str
    agent_name: str
    input_ref: str
    input_digest: str
    spec: dict[str, Any]
    state: Literal["queued", "claimed", "completed", "failed", "canceled"]
    run_id: str = ""
    version: int = Field(ge=1)
    created_at: float
    updated_at: float


class TaskResponse(PublicModel):
    api_version: str = API_VERSION
    task: Task
    idempotent_replay: bool = False


class TaskPage(PublicModel):
    api_version: str = API_VERSION
    data: list[Task]
    next_cursor: str = ""


class CapabilityProfile(PublicModel):
    agent_name: str
    framework: str
    backend: str
    adapter_id: str
    adapter_version: str
    runtime_profile_digest: str
    model_profile_digest: str
    qualification_evidence_digest: str
    qualification_expires_at: float | None = None
    capabilities: dict[str, CapabilityMode]


class CapabilityResponse(PublicModel):
    api_version: str = API_VERSION
    capability_profile: CapabilityProfile


class Approval(PublicModel):
    approval_id: str
    state: str
    version: int = 0
    binding_digest: str = ""
    consequence_summary: str = ""
    risk_class: str = ""
    data_boundary: str = ""
    expires_at: float | None = None


class ApprovalResponse(PublicModel):
    api_version: str = API_VERSION
    approval: Approval


class ApprovalPage(PublicModel):
    api_version: str = API_VERSION
    data: list[Approval]
    next_cursor: str = ""


class Effect(PublicModel):
    effect_id: str
    state: str
    tool_name: str = ""
    effect_class: str = ""
    arguments_digest: str = ""
    result_digest: str = ""
    verification: str = ""


class Evaluation(PublicModel):
    evaluation_id: str
    evaluator_ref: str
    verdict: str
    score: float
    evidence_refs: list[str] = Field(default_factory=list)


class Artifact(PublicModel):
    artifact_id: str
    artifact_ref: str = ""
    artifact_digest: str = ""
    media_type: str = ""
    state: str = ""


class Fork(PublicModel):
    fork_id: str = ""
    parent_run_id: str
    child_run_id: str
    state: str = ""


class Run(PublicModel):
    id: str
    task_id: str
    state: str
    sequence: int = Field(ge=1)
    agent_name: str
    framework: str
    backend: str
    model_ref: str
    runtime_profile_digest: str
    model_profile_digest: str
    qualification_evidence_digest: str
    usage: dict[str, Any]
    budget_enforcement: dict[str, Any]
    effect_count: int = Field(ge=0)
    approval_count: int = Field(ge=0)
    artifact_count: int = Field(ge=0)
    evaluation_count: int = Field(ge=0)
    created_at: float
    updated_at: float
    approvals: list[Approval] = Field(default_factory=list)
    effects: list[Effect] = Field(default_factory=list)
    evaluations: list[Evaluation] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)


class RunResponse(PublicModel):
    api_version: str = API_VERSION
    run: Run


class RunPage(PublicModel):
    api_version: str = API_VERSION
    data: list[Run]
    next_cursor: str = ""


class RunEvent(PublicModel):
    sequence: int = Field(ge=1)
    event_type: str
    event_id: str
    observed_at: float
    created_at: float
    step_id: str = ""
    data: dict[str, Any]
    digest: str


class RunEventPage(PublicModel):
    api_version: str = API_VERSION
    data: list[RunEvent]
    next_cursor: str = ""
    current_sequence: int


class TraceSpan(PublicModel):
    span_id: str
    sequence: int
    name: str
    started_at: float
    attributes: dict[str, Any]
    event_digest: str


class Trace(PublicModel):
    trace_id: str
    run_id: str
    state: str
    framework: str
    model_ref: str
    visibility: str
    started_at: float
    finished_at: float
    duration_ms: float
    usage: dict[str, Any]
    usage_precision: str
    budget_enforcement: dict[str, Any]
    effect_count: int
    approval_count: int
    artifact_count: int
    evaluation_count: int
    spans: list[TraceSpan]
    trace_digest: str


class TraceResponse(PublicModel):
    api_version: str = API_VERSION
    trace: Trace


class ApprovalDecision(StrictInput):
    decision_id: str
    decision: Literal["approve", "reject"]
    expected_approval_sequence: int = Field(ge=1)
    binding_digest: str
    reason_code: str


class CancelRequest(StrictInput):
    cancellation_id: str
    expected_sequence: int = Field(ge=1)
    reason_code: str


class EvaluationCreate(StrictInput):
    evaluation_id: str
    expected_sequence: int = Field(ge=1)
    evaluator_ref: str
    verdict: str
    score: float = Field(ge=0, le=1)
    evidence_refs: list[str] = Field(default_factory=list)


class ForkCreate(StrictInput):
    fork_id: str
    child_run_id: str
    expected_sequence: int = Field(ge=1)
    reason_code: str


class PackageRecord(PublicModel):
    package_id: str
    name: str
    version: str
    digest: str
    stage: str
    status: str
    project_id: str = ""
    created_at: float = 0
    updated_at: float = 0


class PackageResponse(PublicModel):
    api_version: str = API_VERSION
    package: PackageRecord


class PackagePage(PublicModel):
    api_version: str = API_VERSION
    data: list[PackageRecord]
    next_cursor: str = ""


class PackageUpload(StrictInput):
    name: str
    version: str
    digest: str
    media_type: str
    content_base64: str
    signature_bundle: dict[str, Any] = Field(default_factory=dict)


class PackagePromotion(StrictInput):
    promotion_id: str
    target: Literal["staging", "canary", "production"]
    expected_digest: str


class TypedTask(StrictInput):
    task_id: str = Field(min_length=1, max_length=255)
    context_id: str = Field(min_length=1, max_length=255)
    prompt_digest: str
    framework: str = Field(default="open", max_length=64)
    model_ref: str = Field(default="", max_length=512)
    model_profile_digest: str = Field(default="", max_length=80)
    persona_ref: str = Field(default="", max_length=512)
    policy_ref: str = Field(default="", max_length=512)
    privacy_class: str = Field(default="private", max_length=64)
    budget: dict[str, Any] = Field(default_factory=dict)
    outcome_contract: dict[str, Any] | None = None

    @field_validator("prompt_digest", "model_profile_digest")
    @classmethod
    def validate_digest(cls, value: str, info: Any) -> str:
        normalized = str(value or "").lower()
        if info.field_name == "model_profile_digest" and not normalized:
            return normalized
        if _DIGEST.fullmatch(normalized) is None:
            raise ValueError(f"{info.field_name} must be sha256:<64 lowercase hex>")
        return normalized


TERMINAL_RUN_STATES = frozenset({"completed", "failed", "canceled"})
