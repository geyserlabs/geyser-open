from __future__ import annotations

import json
from pathlib import Path

from conformance.qualification import REQUIRED_CASES


def test_public_emulator_fixture_is_frozen_and_unique() -> None:
    path = Path(__file__).parents[1] / "fixtures" / "emulator-cases.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    assert value["schema_version"] == 1
    assert value["frozen"] is True
    identifiers = [row["case_id"] for row in value["cases"]]
    assert len(identifiers) == len(set(identifiers))
    required = set().union(
        REQUIRED_CASES["protocol_core"],
        REQUIRED_CASES["runtime_adapter"],
        REQUIRED_CASES["provider_transport"],
    )
    assert required <= set(identifiers)
    assert {"ambient-network", "ambient-credentials"} <= set(identifiers)
