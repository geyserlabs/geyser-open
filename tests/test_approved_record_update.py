import asyncio
import importlib.util
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).parents[1] / "examples" / "approved_record_update.py"
spec = importlib.util.spec_from_file_location("approved_record_update", EXAMPLE)
assert spec and spec.loader
example = importlib.util.module_from_spec(spec)
spec.loader.exec_module(example)


@pytest.mark.parametrize("approve,interrupted", [(False, False), (True, False), (True, True)])
def test_exact_approval_and_interrupted_write_recovery(tmp_path, approve, interrupted):
    store = example.TicketStore(tmp_path / "tickets.sqlite")
    store.initialize()
    result = asyncio.run(example.demonstrate(store, approve=approve, lose_response=interrupted))
    assert result["tool_invocations"] == int(approve)
    assert result["record"]["status"] == ("reviewed" if approve else "open")
    assert result["record"]["version"] == (2 if approve else 1)


def test_record_version_and_operation_identity_cannot_drift(tmp_path):
    store = example.TicketStore(tmp_path / "tickets.sqlite")
    store.initialize()
    arguments = {"ticket_id": 42, "expected_version": 1, "status": "reviewed"}
    result = store.update("op-1", arguments)
    assert store.update("op-1", arguments) == result
    with pytest.raises(ValueError, match="another exact change"):
        store.update("op-1", {**arguments, "status": "open"})
    with pytest.raises(ValueError, match="record changed"):
        store.update("op-2", arguments)
    assert store.read()["version"] == 2


def test_example_refuses_to_overwrite_an_existing_database(tmp_path):
    path = tmp_path / "tickets.sqlite"
    path.write_bytes(b"existing file")
    with pytest.raises(FileExistsError):
        example.TicketStore(path).initialize()
    assert path.read_bytes() == b"existing file"
