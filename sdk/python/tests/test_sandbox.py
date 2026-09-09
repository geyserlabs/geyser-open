from __future__ import annotations

import os
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


def test_frozen_cli_uses_installed_python_and_preserves_file_boundary(
    package: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    python_directory = str(Path(sys.executable).resolve().parent)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(package / "geyser"))
    monkeypatch.setenv("PATH", python_directory + os.pathsep + "/usr/bin:/bin")
    monkeypatch.setenv("DYLD_LIBRARY_PATH", str(package / "untrusted-library-directory"))
    (package / "handler.py").write_text('def run(value): return {"count": len(value)}\n')
    assert run_handler(package, "handler.py:run", [1, 2]) == {"count": 2}
    outside = package.parent / "outside-frozen"
    outside.write_text("synthetic-private-value")
    (package / "handler.py").write_text(
        f'def run(value): return {{"count": len(open({str(outside)!r}).read())}}\n'
    )
    with pytest.raises(SandboxError):
        run_handler(package, "handler.py:run", [])


def test_frozen_cli_does_not_probe_package_or_relative_path_candidates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from geyser_sdk.sandbox import _python_runtime

    package = tmp_path / "package"
    package.mkdir()
    marker = tmp_path / "must-not-be-created"
    candidate = package / "python3"
    candidate.write_text(f"#!/bin/sh\ntouch {str(marker)!r}\n")
    candidate.chmod(0o755)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setenv("PATH", str(package) + os.pathsep + "package" + os.pathsep + ".")
    with pytest.raises(SandboxUnavailable, match=r"install Python 3\.11"):
        _python_runtime(package)
    assert not marker.exists()


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
    monkeypatch.setattr("geyser_sdk.sandbox.available", lambda *_args: False)
    with pytest.raises(SandboxUnavailable):
        run_handler(package, "handler.py:run", {})
