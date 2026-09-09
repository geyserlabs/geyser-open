from __future__ import annotations

import socket
import sys
from pathlib import Path

import pytest
from geyser_sdk.sandbox import SandboxError, SandboxUnavailable, available, run_handler


@pytest.fixture
def package(tmp_path: Path) -> Path:
    if not available():
        pytest.skip("this platform has no supported extension sandbox")
    root = tmp_path / "package"
    root.mkdir()
    return root


def test_json_handler_and_ambient_environment(
    package: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GEYSER_SYNTHETIC_SECRET", "must-not-be-inherited")
    (package / "handler.py").write_text(
        'import os\ndef run(value):\n return {"words": len(value["text"].split()), '
        '"secret": os.getenv("GEYSER_SYNTHETIC_SECRET")}\n'
    )
    assert run_handler(package, "handler.py:run", {"text": "hello world"}) == {
        "words": 2,
        "secret": None,
    }


@pytest.mark.parametrize("operation", ["read", "write", "network", "subprocess", "import"])
def test_denies_host_authority_before_and_during_handler(package: Path, operation: str) -> None:
    outside = package.parent / "outside"
    outside.write_text("synthetic-private-value")
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    port = listener.getsockname()[1]
    path = repr(str(outside))
    actions = {
        "read": f"open({path}).read()",
        "write": f"open({path}, 'w').write('changed')",
        "network": f"__import__('socket').create_connection(('127.0.0.1', {port}), timeout=0.2)",
        "subprocess": (
            f"__import__('subprocess').run([{str(Path(sys.executable).resolve())!r}, "
            "'-I', '-S', '-c', 'pass'], check=True)"
        ),
        "import": f"open({path}).read()",
    }
    code = (
        actions[operation] + "\ndef run(value): return value\n"
        if operation == "import"
        else "def run(value):\n " + actions[operation] + "\n return value\n"
    )
    (package / "handler.py").write_text(code)
    with pytest.raises(SandboxError):
        run_handler(package, "handler.py:run", {})
    listener.close()
    assert outside.read_text() == "synthetic-private-value"


def test_bounds_cpu_memory_and_output(package: Path) -> None:
    (package / "handler.py").write_text("def run(value):\n while True: pass\n")
    with pytest.raises(SandboxError, match="deadline"):
        run_handler(package, "handler.py:run", {}, timeout=0.15)
    (package / "handler.py").write_text(
        "import time\ndef run(value):\n x=bytearray(256*1024*1024)\n"
        " time.sleep(1)\n return len(x)\n"
    )
    with pytest.raises(SandboxError):
        run_handler(package, "handler.py:run", {}, memory_bytes=64 * 1024 * 1024)
    (package / "handler.py").write_text("def run(value):\n return 'x' * (2*1024*1024)\n")
    with pytest.raises(SandboxError):
        run_handler(package, "handler.py:run", {})


def test_missing_sandbox_and_path_escape_fail_closed(
    package: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(ValueError):
        run_handler(package, "../handler.py:run", {})
    (package / "handler.py").symlink_to(package.parent / "outside.py")
    with pytest.raises(SandboxError):
        run_handler(package, "handler.py:run", {})
    monkeypatch.setattr("geyser_sdk.sandbox.available", lambda: False)
    with pytest.raises(SandboxUnavailable):
        run_handler(package, "handler.py:run", {})
