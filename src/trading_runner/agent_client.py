"""Native subscription-CLI adapters used by the manual rollout runner."""

from __future__ import annotations

import json
import os
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Protocol


@dataclass(frozen=True, slots=True)
class AgentResult:
    final_response: str
    stdout: str
    stderr: str
    returncode: int
    duration_seconds: float
    command: tuple[str, ...]
    session_id: str | None = None


class AgentClient(Protocol):
    harness: str

    def version(self) -> str:
        ...

    def invoke(
        self,
        *,
        prompt: str,
        workdir: Path,
        model: str,
        reasoning_effort: str,
        session_id: str | None,
        allow_search: bool,
        allow_isolated_python: bool,
        environment: Mapping[str, str],
        timeout_seconds: int,
        output_directory: Path,
    ) -> AgentResult:
        ...


def _version(executable: str) -> str:
    try:
        completed = subprocess.run(
            [executable, "--version"],
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    value = (completed.stdout or completed.stderr).strip()
    return value or "unknown"


def _codex_session_id(stdout: str) -> str | None:
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict) or event.get("type") != "thread.started":
            continue
        session_id = event.get("thread_id")
        if isinstance(session_id, str) and session_id.strip():
            return session_id
    return None


def _json_document(stdout: str) -> object | None:
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return None


def _claude_result(stdout: str) -> tuple[str, str | None]:
    document = _json_document(stdout)
    if not isinstance(document, dict):
        return stdout, None
    value = document.get("result", "")
    final_response = (
        value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    )
    session_id = document.get("session_id")
    return final_response, session_id if isinstance(session_id, str) else None


def _dsh_result(stdout: str) -> tuple[str, str | None]:
    final_response = ""
    session_id = None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "session":
            value = event.get("sessionId")
            if isinstance(value, str) and value:
                session_id = value
        elif event.get("type") == "final":
            value = event.get("text")
            if isinstance(value, str):
                final_response = value
    return final_response, session_id


def _zcode_result(stdout: str) -> tuple[str, str | None]:
    document = _json_document(stdout)
    if not isinstance(document, dict):
        return stdout, None
    value = document.get("response", "")
    final_response = (
        value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    )
    session_id = document.get("sessionId")
    return final_response, session_id if isinstance(session_id, str) else None


def session_id_from_output(harness: str, stdout: str) -> str | None:
    parsers = {
        "codex": lambda value: (None, _codex_session_id(value)),
        "claude": _claude_result,
        "dsh": _dsh_result,
        "zcode": _zcode_result,
    }
    parser = parsers.get(harness)
    return parser(stdout)[1] if parser is not None else None


class CodexClient:
    harness = "codex"

    def __init__(self, executable: str = "codex") -> None:
        self.executable = executable

    def version(self) -> str:
        return _version(self.executable)

    def build_command(
        self,
        *,
        workdir: Path,
        model: str,
        reasoning_effort: str,
        session_id: str | None,
        final_output: Path,
        allow_search: bool,
    ) -> list[str]:
        command = [self.executable]
        if allow_search:
            command.append("--search")
        command.extend([
            "--ask-for-approval",
            "never",
            "exec",
            "--skip-git-repo-check",
            "--color",
            "never",
            "--sandbox",
            "workspace-write",
            "-C",
            str(workdir),
            "--model",
            model,
            "--config",
            f"model_reasoning_effort={reasoning_effort}",
            "--output-last-message",
            str(final_output),
            "--json",
        ])
        if session_id is not None:
            command.extend(["resume", session_id, "-"])
        else:
            command.append("-")
        return command

    def invoke(
        self,
        *,
        prompt: str,
        workdir: Path,
        model: str,
        reasoning_effort: str,
        session_id: str | None,
        allow_search: bool,
        allow_isolated_python: bool,
        environment: Mapping[str, str],
        timeout_seconds: int,
        output_directory: Path,
    ) -> AgentResult:
        final_output = output_directory / "agent_final_raw.md"
        command = self.build_command(
            workdir=workdir,
            model=model,
            reasoning_effort=reasoning_effort,
            session_id=session_id,
            final_output=final_output,
            allow_search=allow_search,
        )
        started = time.monotonic()
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            cwd=workdir,
            env={**os.environ, **environment},
            timeout=timeout_seconds,
            check=False,
        )
        duration = time.monotonic() - started
        final_response = (
            final_output.read_text(encoding="utf-8")
            if final_output.exists()
            else ""
        )
        return AgentResult(
            final_response=final_response,
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
            duration_seconds=duration,
            command=tuple(command),
            session_id=_codex_session_id(completed.stdout) or session_id,
        )


class ClaudeClient:
    harness = "claude"

    def __init__(self, executable: str = "claude") -> None:
        self.executable = executable

    def version(self) -> str:
        return _version(self.executable)

    def build_command(
        self,
        *,
        model: str,
        reasoning_effort: str,
        session_id: str | None,
        initial_session_id: str | None = None,
        allow_search: bool = True,
        allow_isolated_python: bool = False,
    ) -> list[str]:
        tools = ["Read", "Write", "Edit", "Bash"]
        allowed_tools = ["Read", "Write", "Edit", "Bash(./broker *)"]
        if allow_isolated_python:
            allowed_tools.extend(["Bash(python3 *)", "Bash(python *)"])
        denied_tools = ["Agent"]
        if allow_search:
            tools.extend(["WebSearch", "WebFetch"])
            allowed_tools.extend(["WebSearch", "WebFetch"])
        else:
            denied_tools.extend(["WebSearch", "WebFetch"])
        command = [
            self.executable,
            "--print",
            "--output-format",
            "json",
            "--model",
            model,
            "--effort",
            reasoning_effort,
            "--restricted",
            "--permission-mode",
            "dontAsk",
            "--permission-prompts",
            "none",
            "--no-chrome",
            "--tools",
            ",".join(tools),
            "--allowedTools",
            ",".join(allowed_tools),
            "--disallowedTools",
            ",".join(denied_tools),
        ]
        if session_id is not None:
            command.extend(["--resume", session_id])
        elif initial_session_id is not None:
            command.extend(["--session-id", initial_session_id])
        return command

    def invoke(
        self,
        *,
        prompt: str,
        workdir: Path,
        model: str,
        reasoning_effort: str,
        session_id: str | None,
        allow_search: bool,
        allow_isolated_python: bool,
        environment: Mapping[str, str],
        timeout_seconds: int,
        output_directory: Path,
    ) -> AgentResult:
        expected_session_id = session_id or str(uuid.uuid4())
        command = self.build_command(
            model=model,
            reasoning_effort=reasoning_effort,
            session_id=session_id,
            initial_session_id=expected_session_id,
            allow_search=allow_search,
            allow_isolated_python=allow_isolated_python,
        )
        started = time.monotonic()
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            cwd=workdir,
            env={**os.environ, **environment},
            timeout=timeout_seconds,
            check=False,
        )
        duration = time.monotonic() - started
        final_response, reported_session_id = _claude_result(completed.stdout)
        return AgentResult(
            final_response=final_response,
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
            duration_seconds=duration,
            command=tuple(command),
            session_id=reported_session_id or expected_session_id,
        )


class DshClient:
    harness = "dsh"

    def __init__(self, executable: str = "dsh") -> None:
        self.executable = executable

    def version(self) -> str:
        return _version(self.executable)

    def build_command(self, *, session_id: str | None) -> list[str]:
        command = [self.executable, "headless", "--json"]
        if session_id is not None:
            command.extend(["--session-id", session_id])
        command.append("-")
        return command

    def invoke(
        self,
        *,
        prompt: str,
        workdir: Path,
        model: str,
        reasoning_effort: str,
        session_id: str | None,
        allow_search: bool,
        allow_isolated_python: bool,
        environment: Mapping[str, str],
        timeout_seconds: int,
        output_directory: Path,
    ) -> AgentResult:
        command = self.build_command(session_id=session_id)
        started = time.monotonic()
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            cwd=workdir,
            env={**os.environ, **environment},
            timeout=timeout_seconds,
            check=False,
        )
        duration = time.monotonic() - started
        final_response, reported_session_id = _dsh_result(completed.stdout)
        return AgentResult(
            final_response=final_response,
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
            duration_seconds=duration,
            command=tuple(command),
            session_id=reported_session_id or session_id,
        )


class ZCodeClient:
    harness = "zcode"

    def __init__(self, executable: str = "zcode") -> None:
        self.executable = executable

    def version(self) -> str:
        return _version(self.executable)

    def build_command(
        self,
        *,
        prompt: str,
        workdir: Path,
        session_id: str | None,
        allow_search: bool,
    ) -> list[str]:
        denied = ["Agent"]
        if not allow_search:
            denied.extend(["WebSearch", "WebFetch", "Browser"])
        command = [
            self.executable,
            "--cwd",
            str(workdir),
            "--mode",
            "guarded",
            "--workflow-mode",
            "disabled",
            "--disallowed-tools",
            ",".join(denied),
            "--json",
            "--no-color",
        ]
        if session_id is not None:
            command.extend(["--resume", session_id])
        command.extend(["--prompt", prompt])
        return command

    def invoke(
        self,
        *,
        prompt: str,
        workdir: Path,
        model: str,
        reasoning_effort: str,
        session_id: str | None,
        allow_search: bool,
        allow_isolated_python: bool,
        environment: Mapping[str, str],
        timeout_seconds: int,
        output_directory: Path,
    ) -> AgentResult:
        command = self.build_command(
            prompt=prompt,
            workdir=workdir,
            session_id=session_id,
            allow_search=allow_search,
        )
        started = time.monotonic()
        completed = subprocess.run(
            command,
            text=True,
            capture_output=True,
            cwd=workdir,
            env={**os.environ, **environment},
            timeout=timeout_seconds,
            check=False,
        )
        duration = time.monotonic() - started
        final_response, reported_session_id = _zcode_result(completed.stdout)
        return AgentResult(
            final_response=final_response,
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
            duration_seconds=duration,
            command=tuple(command),
            session_id=reported_session_id or session_id,
        )
