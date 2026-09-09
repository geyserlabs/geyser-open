"""Run a synchronous JSON handler with no credentials or ambient host authority.

Only the standard library and a private package snapshot are readable. Linux
requires bubblewrap plus a syscall filter; macOS requires sandbox-exec. There is
no unsandboxed fallback. This module is also vendored by the Geyser Agent.
"""

from __future__ import annotations

import ctypes
import json
import math
import os
import platform
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
from functools import lru_cache
from pathlib import Path
from typing import Any

MAX_BYTES = 1024 * 1024
IGNORED = {".git", ".geyser", ".venv", "__pycache__"}
PYTHON_REQUIRED = "install Python 3.11 or newer to execute extensions with the standalone CLI"


class SandboxError(RuntimeError):
    pass


class SandboxUnavailable(SandboxError):
    pass


_BOOTSTRAP = r"""
import sys, os, json, resource, importlib.util, platform
resource.setrlimit(resource.RLIMIT_CPU, (int(sys.argv[3]), int(sys.argv[3])))
resource.setrlimit(resource.RLIMIT_FSIZE, (1048576, 1048576))
resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
if sys.platform == 'linux':
    resource.setrlimit(resource.RLIMIT_AS, (int(sys.argv[4]), int(sys.argv[4])))
    import ctypes
    machine = platform.machine()
    if machine in {'x86_64', 'amd64'}:
        arch = 0xc000003e
        denied = [41,42,53,56,57,58,59,101,165,166,272,308,310,311,322,435]
    elif machine in {'aarch64', 'arm64'}:
        arch = 0xc00000b7
        denied = [39,40,97,117,198,199,203,220,221,268,270,271,281,435]
    else:
        raise RuntimeError('unsupported sandbox architecture')
    class Filter(ctypes.Structure):
        _fields_ = [('code', ctypes.c_ushort), ('jt', ctypes.c_ubyte),
                    ('jf', ctypes.c_ubyte), ('k', ctypes.c_uint)]
    class Program(ctypes.Structure):
        _fields_ = [('length', ctypes.c_ushort), ('filters', ctypes.POINTER(Filter))]
    rules = [(0x20,0,0,4), (0x15,1,0,arch), (0x06,0,0,0x80000000), (0x20,0,0,0)]
    # x32 shares AUDIT_ARCH_X86_64 but adds an ABI bit to syscall numbers.
    # Reject that ABI before comparing the native syscall deny list.
    if machine in {'x86_64', 'amd64'}:
        rules += [(0x35,0,1,0x40000000), (0x06,0,0,0x80000000)]
    for number in denied:
        rules += [(0x15,0,1,number), (0x06,0,0,0x00050001)]
    rules += [(0x06,0,0,0x7fff0000)]
    filters = (Filter * len(rules))(*(Filter(*rule) for rule in rules))
    program = Program(len(rules), filters)
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(38, 1, 0, 0, 0) != 0 or libc.prctl(22, 2, ctypes.byref(program), 0, 0) != 0:
        raise RuntimeError('sandbox syscall filter unavailable')
    resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))
path, symbol = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.dirname(path))
spec = importlib.util.spec_from_file_location('geyser_extension', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
value = getattr(module, symbol)(json.loads(sys.stdin.buffer.read(1048577)))
sys.stdout.write(json.dumps(value, allow_nan=False, separators=(',', ':')))
"""


def _snapshot(root: Path, target: Path) -> None:
    size = entries = 0

    def visit(directory: int, destination: Path) -> None:
        nonlocal size, entries
        with os.scandir(directory) as stream:
            for entry in stream:
                if entry.name in IGNORED:
                    continue
                entries += 1
                if entries > 512:
                    raise SandboxError("package exceeds snapshot bounds")
                mode = entry.stat(follow_symlinks=False).st_mode
                if stat.S_ISDIR(mode):
                    child = os.open(
                        entry.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY, dir_fd=directory
                    )
                    try:
                        (destination / entry.name).mkdir()
                        visit(child, destination / entry.name)
                    finally:
                        os.close(child)
                elif stat.S_ISREG(mode):
                    descriptor = os.open(
                        entry.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory
                    )
                    with os.fdopen(descriptor, "rb") as source:
                        if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                            raise SandboxError("package changed during snapshot")
                        content = source.read(2 * MAX_BYTES + 1)
                    size += len(content)
                    if len(content) > 2 * MAX_BYTES or size > 10 * MAX_BYTES:
                        raise SandboxError("package exceeds snapshot bounds")
                    (destination / entry.name).write_bytes(content)
                else:
                    raise SandboxError("package contains an unsafe file type")

    try:
        directory = os.open(root, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
        try:
            visit(directory, target)
        finally:
            os.close(directory)
    except OSError as exc:
        raise SandboxError("package changed during snapshot") from exc


def _python_runtime(source_root: Path | None = None) -> tuple[str, str]:
    if not getattr(sys, "frozen", False):
        return str(Path(sys.executable).resolve()), str(Path(sys.base_prefix).resolve())
    # The frozen CLI is not a Python command-line interpreter. Probe only an
    # installed interpreter, never a package/current-directory PATH candidate.
    excluded = {Path.cwd().resolve()}
    if source_root is not None:
        excluded.add(source_root.resolve())
    seen = set()
    for entry in os.get_exec_path():
        directory = Path(entry)
        if not directory.is_absolute():
            continue
        for name in ("python3", "python3.13", "python3.12", "python3.11"):
            executable = (directory / name).resolve()
            if executable in seen or any(executable.is_relative_to(root) for root in excluded):
                continue
            seen.add(executable)
            if not executable.is_file() or not os.access(executable, os.X_OK):
                continue
            try:
                with tempfile.TemporaryDirectory(prefix="geyser-python-probe-") as probe:
                    result = subprocess.run(  # noqa: S603 - fixed code in installed Python
                        [str(executable), "-I", "-S", "-c",
                         "import json,sys; print(json.dumps([list(sys.version_info[:2]),"
                         "sys.executable,sys.base_prefix]))"],
                        cwd=probe, capture_output=True, timeout=3, check=False,
                        env={"LANG": "C.UTF-8"},
                    )
                version, actual, prefix = json.loads(result.stdout)
                actual, prefix = Path(actual).resolve(), Path(prefix).resolve()
                if (result.returncode == 0 and version[0] == 3 and version[1] >= 11
                        and actual.is_file() and prefix.is_dir()
                        and not any(actual.is_relative_to(root) or prefix.is_relative_to(root)
                                    for root in excluded)):
                    return str(actual), str(prefix)
            except (OSError, ValueError, TypeError, IndexError, subprocess.TimeoutExpired):
                continue
    raise SandboxUnavailable(PYTHON_REQUIRED)


@lru_cache(maxsize=1)
def available(interpreter: tuple[str, str] | None = None) -> bool:
    executable_available = bool(
        (sys.platform == "darwin" and shutil.which("sandbox-exec"))
        or (
            sys.platform == "linux"
            and shutil.which("bwrap")
            and platform.machine() in {"x86_64", "amd64", "aarch64", "arm64"}
        )
    )
    if not executable_available:
        return False
    # A binary on PATH does not prove namespaces or the sandbox policy work.
    # Probe the actual bootstrap before advertising executable capability.
    try:
        with tempfile.TemporaryDirectory(prefix="geyser-sandbox-probe-") as temporary:
            root = Path(temporary).resolve()
            (root / "handler.py").write_text("def run(value): return value\n")
            result = subprocess.run(  # noqa: S603 - fixed interpreter inside the OS sandbox
                _command(root, root, "handler.py", "run", 2, 512 * MAX_BYTES,
                         interpreter=interpreter),
                input=b"{}",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
                env={"LANG": "C.UTF-8"},
                close_fds=True,
                check=False,
            )
            return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired, SandboxUnavailable):
        return False


def _mac_memory_reader() -> Any:
    # Darwin does not implement RLIMIT_AS. The trusted parent samples only its
    # child through libproc and kills it on excess RSS. This is a watchdog, not
    # a kernel allocation ceiling; Linux uses the hard address-space ceiling.
    library = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
    function = library.proc_pidinfo
    function.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
    function.restype = ctypes.c_int

    def resident(pid: int) -> int:
        information = ctypes.create_string_buffer(96)
        if function(pid, 4, 0, information, 96) != 96:
            raise SandboxUnavailable("cannot inspect sandbox memory use")
        return int.from_bytes(information.raw[8:16], sys.byteorder)

    resident(os.getpid())  # Fail before starting any extension if unavailable.
    return resident


def _command(
    root: Path, writable: Path, handler: str, symbol: str, seconds: float, memory: int,
    *, interpreter: tuple[str, str] | None = None,
) -> list[str]:
    executable, runtime = interpreter or _python_runtime(root)
    if sys.platform == "darwin":
        # Framework Python's bin/python is a launcher that starts Python.app.
        # Execute the real interpreter so the policy permits exactly one binary.
        framework_python = Path(runtime) / "Resources/Python.app/Contents/MacOS/Python"
        if framework_python.is_file():
            executable = str(framework_python.resolve())
    arguments = [
        executable,
        "-I",
        "-S",
        "-c",
        _BOOTSTRAP,
        str(root / handler),
        symbol,
        str(max(1, math.ceil(seconds))),
        str(memory),
    ]
    if sys.platform == "darwin" and (sandbox := shutil.which("sandbox-exec")):

        def literal(path: str | Path) -> str:
            return json.dumps(str(path))

        # realpath() needs metadata on parent directories, even when the target
        # itself is readable. This permits no contents of those directories.
        parents = set(Path(executable).parents) | set(root.parents) | set(writable.parents)
        parent_metadata = " ".join(f"(literal {literal(path)})" for path in sorted(parents))
        policy = "\n".join(
            [
                "(version 1)",
                "(deny default)",
                f"(allow file-read-metadata {parent_metadata})",
                f"(allow process-exec (literal {literal(executable)}))",
                f"(allow file-read* (subpath {literal(root)}) (subpath {literal(runtime)}) "
                '(subpath "/System/Library") (subpath "/usr/lib") '
                '(literal "/") (literal "/dev/null") (literal "/dev/urandom"))',
                f"(allow file-read* file-write* (subpath {literal(writable)}))",
            ]
        )
        return [sandbox, "-p", policy, *arguments]
    if sys.platform == "linux" and (sandbox := shutil.which("bwrap")):
        command = [
            sandbox,
            "--die-with-parent",
            "--new-session",
            "--unshare-all",
            "--unshare-user",
            "--cap-drop",
            "ALL",
            "--clearenv",
            "--dev",
            "/dev",
            "--tmpfs",
            "/tmp",  # noqa: S108 - private tmpfs inside the new mount namespace
        ]
        for path in dict.fromkeys([runtime, "/usr/lib", "/lib", "/lib64", str(root)]):
            if Path(path).exists():
                command += ["--ro-bind", path, path]
        command += [
            "--setenv",
            "LD_LIBRARY_PATH",
            str(Path(runtime) / "lib"),
            "--chdir",
            str(root),
            "--",
            *arguments,
        ]
        return command
    raise SandboxUnavailable(
        "install bubblewrap on Linux or enable sandbox-exec on macOS; execution is disabled"
    )


def run_handler(
    root: Path,
    handler: str,
    value: Any,
    *,
    timeout: float = 5.0,
    memory_bytes: int = 512 * MAX_BYTES,
    cancel_event: threading.Event | None = None,
) -> Any:
    """Execute ``relative_file.py:function`` with JSON stdin/stdout and no I/O grants."""
    root = root.expanduser().resolve()
    interpreter = _python_runtime(root)
    if not available(interpreter):
        raise SandboxUnavailable("a supported OS sandbox is required to execute extensions")
    if not 0 < timeout <= 30 or not 64 * MAX_BYTES <= memory_bytes <= 1024 * MAX_BYTES:
        raise ValueError("sandbox bounds must be 0-30 seconds and 64-1024 MiB")
    parts = handler.split(":")
    if len(parts) != 2 or not parts[1].isidentifier():
        raise ValueError("handler must be relative_file.py:function")
    relative = Path(parts[0])
    if relative.is_absolute() or ".." in relative.parts or relative.suffix != ".py":
        raise ValueError("handler must remain inside its package")
    payload = json.dumps(value, allow_nan=False).encode()
    if len(payload) > MAX_BYTES:
        raise ValueError("handler input exceeds 1 MiB")
    memory_reader = _mac_memory_reader() if sys.platform == "darwin" else None
    with tempfile.TemporaryDirectory(prefix="geyser-sandbox-") as temporary:
        snapshot, writable = (
            Path(temporary).resolve() / "package",
            Path(temporary).resolve() / "tmp",
        )
        snapshot.mkdir()
        writable.mkdir()
        _snapshot(root, snapshot)
        if not (snapshot / relative).is_file():
            raise ValueError("handler file is missing")
        command = _command(snapshot, writable, parts[0], parts[1], timeout, memory_bytes,
                           interpreter=interpreter)
        with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
            process = subprocess.Popen(  # noqa: S603 - isolated interpreter; no shell or inherited authority
                command,
                stdin=subprocess.PIPE,
                stdout=output,
                stderr=errors,
                cwd=snapshot,
                env={"LANG": "C.UTF-8", "TMPDIR": str(writable)},
                close_fds=True,
                start_new_session=True,
            )
            stopped = threading.Event()
            memory_exceeded = threading.Event()

            def watch_memory() -> None:
                inspection_failures = 0
                while not stopped.is_set() and process.poll() is None:
                    if cancel_event is not None and cancel_event.is_set():
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        return
                    try:
                        if memory_reader is None or memory_reader(process.pid) <= memory_bytes:
                            inspection_failures = 0
                            stopped.wait(0.01)
                            continue
                    except SandboxUnavailable:
                        if process.poll() is not None:
                            return
                        inspection_failures += 1
                        if inspection_failures < 3:
                            stopped.wait(0.01)
                            continue
                    memory_exceeded.set()
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    return

            watcher = (
                threading.Thread(target=watch_memory, daemon=True)
                if memory_reader or cancel_event
                else None
            )
            if watcher is not None:
                watcher.start()
            try:
                process.communicate(payload, timeout=timeout)
            except BaseException as exc:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                if isinstance(exc, subprocess.TimeoutExpired):
                    raise SandboxError("extension exceeded its execution deadline") from None
                raise
            finally:
                stopped.set()
                if watcher is not None:
                    watcher.join(timeout=1)
            if memory_exceeded.is_set():
                raise SandboxError(
                    "extension exceeded its memory bound or memory inspection failed"
                )
            if process.returncode:
                raise SandboxError("extension failed inside the sandbox")
            output.seek(0)
            result = output.read(MAX_BYTES + 1)
            if len(result) > MAX_BYTES:
                raise SandboxError("extension output exceeds 1 MiB")
            try:
                return json.loads(result)
            except (ValueError, UnicodeError) as exc:
                raise SandboxError("extension did not return one JSON value") from exc
