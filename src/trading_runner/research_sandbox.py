"""Audited, namespace-isolated Python launcher for Claude V2 research."""

from __future__ import annotations

import base64
import ctypes
import hashlib
import json
import os
import resource
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_MAX_OUTPUT = 2 * 1024 * 1024
_TIMEOUT = 120
_PR_SET_NO_NEW_PRIVS = 38
_PR_CAPBSET_DROP = 24


class SandboxError(RuntimeError):
    pass


def _write_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _validated_directory(name: str) -> Path:
    value = os.environ.get(name)
    if not value:
        raise SandboxError(f"missing trusted launcher setting: {name}")
    path = Path(value).resolve(strict=True)
    if not path.is_dir():
        raise SandboxError(f"trusted launcher path is not a directory: {name}")
    return path


def _normalize_script_argument(
    arguments: list[str], workspace: Path, research: Path
) -> list[str]:
    normalized = list(arguments)
    if "-c" in normalized or "-m" in normalized:
        return normalized
    for index, value in enumerate(normalized):
        if value.startswith("-"):
            continue
        supplied = Path(value)
        candidate = (workspace / supplied).resolve() if supplied.parts[:1] == ("research",) else (research / supplied).resolve()
        try:
            relative = candidate.relative_to(research)
        except ValueError as error:
            raise SandboxError("research script must stay inside research/") from error
        normalized[index] = str(relative)
        break
    return normalized


def _source_snapshot(arguments: list[str], research: Path) -> tuple[bytes, str]:
    if "-c" in arguments:
        index = arguments.index("-c")
        if index + 1 >= len(arguments):
            raise SandboxError("python -c requires source code")
        return arguments[index + 1].encode("utf-8"), "inline.py"
    for value in arguments:
        if value.startswith("-"):
            continue
        candidate = (research / value).resolve()
        try:
            candidate.relative_to(research)
        except ValueError as error:
            raise SandboxError("research script must stay inside research/") from error
        if candidate.is_file():
            return candidate.read_bytes(), candidate.name
        break
    return b"", "no_source.py"


def _mount(*arguments: str) -> None:
    completed = subprocess.run(
        ["mount", *arguments], text=True, capture_output=True, check=False
    )
    if completed.returncode != 0:
        raise SandboxError(completed.stderr.strip() or "mount failed")


def _copy_host_file(root: Path, path: str) -> None:
    source = Path(path)
    if not source.exists():
        return
    target = root / source.relative_to("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        _mount("--bind", str(source), str(target))
    else:
        shutil.copy2(source, target)


def _bind_read_only_directory(root: Path, path: str) -> None:
    source = Path(path)
    if not source.is_dir():
        return
    target = root / source.relative_to("/")
    target.mkdir(parents=True, exist_ok=True)
    _mount("--bind", str(source), str(target))
    _mount("-o", "remount,bind,ro", str(target))


def _copy_runtime_libraries(root: Path, python_env: Path) -> None:
    completed = subprocess.run(
        ["ldd", str(python_env / "bin" / "python3")],
        text=True, capture_output=True, check=True,
    )
    paths: set[Path] = set()
    for line in completed.stdout.splitlines():
        fields = line.strip().split()
        for field in fields:
            if field.startswith("/"):
                paths.add(Path(field))
                break
    paths.update(Path("/lib/x86_64-linux-gnu").glob("libnss_*.so.2"))
    paths.update(Path("/lib/x86_64-linux-gnu").glob("libresolv.so.*"))
    for source in paths:
        if not source.is_file() or python_env in source.parents:
            continue
        target = root / source.relative_to("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _drop_privileges() -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    for capability in range(0, 64):
        libc.prctl(_PR_CAPBSET_DROP, capability, 0, 0, 0)
    if libc.prctl(_PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "cannot set no_new_privs")


def _limits() -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (_TIMEOUT, _TIMEOUT))
    resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
    resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
    resource.setrlimit(resource.RLIMIT_FSIZE, (100 * 1024**2, 100 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def _child(encoded: str, arguments: list[str]) -> int:
    config = json.loads(base64.urlsafe_b64decode(encoded.encode("ascii")))
    root = Path(config["root"])
    research = Path(config["research"])
    python_env = Path(config["python_env"])
    decisions = Path(config["decisions"])
    universe = Path(config["universe"])

    root.mkdir(parents=True, exist_ok=True)
    _mount("-t", "tmpfs", "-o", "size=768m,mode=755", "tmpfs", str(root))
    for relative in (
        "bin", "dev", "etc", "etc/ssl", "lib", "lib64", "opt/finance",
        "proc", "tmp", "usr", "workspace/input", "workspace/research",
        "overlay/upper", "overlay/work",
    ):
        (root / relative).mkdir(parents=True, exist_ok=True)

    _copy_runtime_libraries(root, python_env)
    shutil.copytree("/etc/ssl/certs", root / "etc" / "ssl" / "certs", dirs_exist_ok=True)
    _copy_host_file(root, "/etc/ssl/openssl.cnf")
    for host_file in (
        "/etc/resolv.conf", "/etc/hosts", "/etc/nsswitch.conf",
        "/etc/localtime", "/etc/ca-certificates.conf",
    ):
        _copy_host_file(root, host_file)
    _bind_read_only_directory(root, "/usr/share/zoneinfo")
    for device in ("null", "zero", "random", "urandom"):
        target = root / "dev" / device
        target.touch()
        _mount("--bind", f"/dev/{device}", str(target))

    overlay = root / "opt" / "finance"
    options = (
        f"lowerdir={python_env},upperdir={root / 'overlay/upper'},"
        f"workdir={root / 'overlay/work'}"
    )
    _mount("-t", "overlay", "overlay", "-o", options, str(overlay))
    _mount("--bind", str(research), str(root / "workspace" / "research"))
    _mount("-t", "proc", "proc", str(root / "proc"))

    shutil.copy2(universe, root / "workspace" / "input" / "universe.txt")
    shutil.copy2(decisions, root / "workspace" / "input" / "DECISIONS.md")
    for path in (root / "workspace" / "input").iterdir():
        path.chmod(0o444)
    input_directory = root / "workspace" / "input"
    _mount("--bind", str(input_directory), str(input_directory))
    _mount("-o", "remount,bind,ro", str(input_directory))

    os.chroot(root)
    os.chdir("/workspace/research")
    _limits()
    _drop_privileges()
    clean_environment = {
        "HOME": "/tmp",
        "PATH": "/opt/finance/bin",
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONTZPATH": "/usr/share/zoneinfo",
        "SSL_CERT_DIR": "/etc/ssl/certs",
        "LANG": "C.UTF-8",
    }
    os.execve("/opt/finance/bin/python3", ["python3", *arguments], clean_environment)
    return 127


def _capture(command: list[str]) -> tuple[int, bytes, bytes, bool, float]:
    started = time.monotonic()
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        start_new_session=True, close_fds=True,
    )
    assert process.stdout is not None and process.stderr is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    truncated = False
    deadline = started + _TIMEOUT
    while selector.get_map():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            os.killpg(process.pid, signal.SIGKILL)
            truncated = True
            break
        for key, _ in selector.select(min(remaining, 0.2)):
            chunk = os.read(key.fileobj.fileno(), 65536)
            if not chunk:
                selector.unregister(key.fileobj)
                continue
            buffer = buffers[key.data]
            room = _MAX_OUTPUT - len(buffer)
            if room > 0:
                buffer.extend(chunk[:room])
            if len(chunk) > room:
                truncated = True
                os.killpg(process.pid, signal.SIGKILL)
                selector.close()
                break
    try:
        returncode = process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        returncode = process.wait()
    return returncode, bytes(buffers["stdout"]), bytes(buffers["stderr"]), truncated, time.monotonic() - started


def _parent(arguments: list[str]) -> int:
    workspace = _validated_directory("TRADING_RESEARCH_WORKSPACE")
    audit_root = _validated_directory("TRADING_RESEARCH_AUDIT_DIR")
    python_env = _validated_directory("TRADING_RESEARCH_PYTHON_ENV")
    research = (workspace / "research").resolve(strict=True)
    if research.parent != workspace:
        raise SandboxError("research directory escaped the workspace")
    decisions = workspace / "DECISIONS.md"
    universe = workspace / "universe.txt"
    if not decisions.is_file() or not universe.is_file():
        raise SandboxError("research inputs are missing")

    arguments = _normalize_script_argument(arguments, workspace, research)

    source, source_name = _source_snapshot(arguments, research)
    snapshot_name = "source_snapshot.py"
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ") + "-" + uuid.uuid4().hex[:8]
    audit = audit_root / run_id
    audit.mkdir(mode=0o700)
    source_path = audit / snapshot_name
    source_path.write_bytes(source)
    source_path.chmod(0o400)
    with tempfile.TemporaryDirectory(prefix="claude-research-") as temporary:
        config = {
            "root": str(Path(temporary) / "root"), "research": str(research),
            "python_env": str(python_env), "decisions": str(decisions),
            "universe": str(universe),
        }
        encoded = base64.urlsafe_b64encode(
            json.dumps(config, separators=(",", ":")).encode("utf-8")
        ).decode("ascii")
        command = [
            "unshare", "--user", "--map-root-user", "--mount", "--pid",
            "--fork", sys.executable, str(Path(__file__).resolve()),
            "--sandbox-child", encoded, *arguments,
        ]
        returncode, stdout, stderr, truncated, duration = _capture(command)

    (audit / "stdout.log").write_bytes(stdout)
    (audit / "stderr.log").write_bytes(stderr)
    _write_json(audit / "metadata.json", {
        "run_id": run_id, "occurred_at": datetime.now(timezone.utc).isoformat(),
        "argv": arguments, "source_file": source_name, "source_snapshot": snapshot_name,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "returncode": returncode, "duration_seconds": duration,
        "output_truncated": truncated, "stdout_bytes": len(stdout),
        "stderr_bytes": len(stderr),
    })
    sys.stdout.buffer.write(stdout)
    sys.stderr.buffer.write(stderr)
    if truncated:
        sys.stderr.write("\n[research sandbox: output or time limit reached]\n")
    return returncode


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    try:
        if arguments[:1] == ["--sandbox-child"]:
            if len(arguments) < 2:
                raise SandboxError("missing sandbox configuration")
            return _child(arguments[1], arguments[2:])
        return _parent(arguments)
    except Exception as error:
        sys.stderr.write(f"research sandbox error: {error}\n")
        return 126


if __name__ == "__main__":
    raise SystemExit(main())
