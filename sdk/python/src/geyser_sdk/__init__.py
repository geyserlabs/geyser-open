"""Public, framework-neutral Geyser SDK."""

from ._json import bytes_digest, canonical_bytes, digest
from .client import AsyncGeyserClient, GeyserClient, TokenProvider
from .emulator import EmulatorError, LocalEmulator
from .errors import (
    GeyserError,
    Problem,
    ProblemError,
    ResponseValidationError,
    TransportError,
)
from .models import *  # noqa: F403 - typed contract is the intentional public surface
from .structured_outcomes import (
    OutcomeContractError,
    OutcomeValidationError,
    checkpoint_value,
    evidence_refs,
    normalize_contract,
    parse_candidate,
    pydantic_output_type,
    validate_outcome,
)

__version__ = "0.1.0b1"

__all__ = [
    "AsyncGeyserClient",
    "EmulatorError",
    "GeyserClient",
    "GeyserError",
    "LocalEmulator",
    "OutcomeContractError",
    "OutcomeValidationError",
    "Problem",
    "ProblemError",
    "ResponseValidationError",
    "TokenProvider",
    "TransportError",
    "bytes_digest",
    "canonical_bytes",
    "checkpoint_value",
    "digest",
    "evidence_refs",
    "normalize_contract",
    "parse_candidate",
    "pydantic_output_type",
    "validate_outcome",
]
