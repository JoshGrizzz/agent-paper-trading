"""One-shot orchestration without scheduling or cross-rollout concurrency."""

from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping
from zoneinfo import ZoneInfo

from .agent_client import (
    AgentClient,
    ClaudeClient,
    CodexClient,
    DshClient,
    ZCodeClient,
    session_id_from_output,
)


_NEW_YORK = ZoneInfo("America/New_York")
_ROLLOUT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

FIXED_PROMPT = """你正在参加一个美股模拟交易比赛。你的目标是在比赛结束时尽可能提高账户价值。

请实际阅读当前工作目录中的 BROKER.md、universe.txt、DECISION_FORMAT.md 和 DECISIONS.md，并遵守其中的全部规则。优先使用专用文件读取工具；若没有专用读取工具但普通 shell 可用，可以使用 sed 等只读命令读取这四个文件。不得读取其他 rollout。DECISIONS.md 只包含你自己的历史决策；账户、持仓、订单和成交状态始终以 ./broker 返回的结果为准。

首先执行 ./broker status --json。你负责自主研究、决策和交易；每轮可提交一个含主方案和最多两个 backup 的限价方案，也可以撤销当前方案或不操作。只能通过 ./broker 提交或撤销方案，不得直接读取或修改 .broker 中的账户文件。

提交前必须使用 status 返回的 cash.available 和 positions[].available_quantity 做预算：分别计算每个候选方案全部买单的 Σ(数量 × 限价)，每个候选都必须独立负担得起；不同候选互斥，预计冻结现金取有效候选资金需求的最大值，而不是相加。不得把预计卖出收入用于支付同一候选方案的买单，也不得卖出超过 available_quantity 的股份。

完成操作后再次查看账户状态，并逐项确认主方案和每个 backup 是否被接受。你的预算仅用于决策说明，最终结果始终以 broker 的独立校验为准。

若 harness 实际对 Bash 使用命令白名单：请使用文件写入工具单独创建 PLAN.json；每次 Bash 调用只能执行一条以 `./broker` 开头的命令。不要把 `cat`、`mkdir`、`cd`、重定向、管道、分号、`echo` 或第二条命令与 `./broker` 拼在同一次 Bash 调用中。提交和随后查询状态必须分成两次独立的 `./broker` 调用。不要仅因本提示提到白名单就假定当前 harness 禁止读取文件；有专用读取工具时，读取文件不属于 Bash 调用。

不得创建子 Agent、并行 Agent 或委派任务。不要修改 broker、共享规则文件、DECISIONS.md 或 .runner；每轮结束时，最终回复必须且只能包含一条符合 DECISION_FORMAT.md 的决策记录，runner 会自动追加该记录。`### 本轮判断`、`### 资金与持仓检查`、`### 本轮操作`、`### 后续计划` 四个标题必须分别独占一行，并保留三个 `#`，不得改写成列表项或加粗文本。`### 本轮操作` 必须明确包含 `提交交易方案`、`撤销交易方案` 或 `不操作` 三者之一。
"""


class RunnerError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class RunConfig:
    rollout_id: str
    harness: str
    model: str
    as_of: datetime
    timeout_seconds: int = 900
    reasoning_effort: str = "medium"
    project_root: Path = _PROJECT_ROOT
    rollouts_root: Path | None = None
    frozen_time: bool = False

    def __post_init__(self) -> None:
        if not _ROLLOUT_ID.fullmatch(self.rollout_id):
            raise ValueError("rollout_id must contain only letters, numbers, _ or -")
        if self.harness not in {"codex", "claude", "dsh", "zcode"}:
            raise ValueError("harness must be codex, claude, dsh or zcode")
        if not self.model.strip():
            raise ValueError("model must not be empty")
        if self.reasoning_effort not in {"low", "medium", "high", "xhigh", "max"}:
            raise ValueError("unsupported reasoning_effort")
        if self.as_of.tzinfo is None or self.as_of.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    @property
    def rollout_directory(self) -> Path:
        root = self.rollouts_root or self.project_root / "rollouts"
        return root / self.rollout_id


@dataclass(frozen=True, slots=True)
class BrokerResult:
    document: dict[str, Any]
    stdout: str
    stderr: str
    returncode: int


BrokerCall = Callable[[Path, str, Mapping[str, str], datetime, int], BrokerResult]


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with temporary.open("wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _write_text(path: Path, content: str) -> None:
    _atomic_write(path, content.encode("utf-8"))


def initialize_rollout(config: RunConfig) -> Path:
    directory = config.rollout_directory
    directory.mkdir(parents=True, exist_ok=True)
    (directory / ".broker").mkdir(exist_ok=True)
    (directory / ".runner" / "logs").mkdir(parents=True, exist_ok=True)

    shared = {
        "BROKER.md": config.project_root / "BROKER.md",
        "universe.txt": config.project_root / "universe.txt",
        "DECISION_FORMAT.md": config.project_root / "templates" / "DECISION_FORMAT.md",
    }
    for name, source in shared.items():
        if not source.is_file():
            raise RunnerError(f"missing shared file: {source}")
        target = directory / name
        source_bytes = source.read_bytes()
        if target.is_symlink():
            if target.resolve() != source.resolve():
                raise RunnerError(f"unexpected shared-file symlink: {target}")
            target.unlink()
        elif target.exists():
            if not target.is_file() or target.read_bytes() != source_bytes:
                raise RunnerError(
                    f"rollout rule snapshot does not match project source: {target}"
                )
        if not target.exists():
            _atomic_write(target, source_bytes)
        target.chmod(0o444)

    decisions = directory / "DECISIONS.md"
    if not decisions.exists():
        template = config.project_root / "templates" / "DECISIONS.md"
        _atomic_write(decisions, template.read_bytes())

    broker_source = config.project_root / "broker"
    if not broker_source.is_file():
        raise RunnerError(f"missing broker executable: {broker_source}")
    launcher = directory / "broker"
    launcher_lines = [
        "#!/bin/sh",
        f"export BROKER_DATA_DIR={shlex.quote(str(directory / '.broker'))}",
        f"export BROKER_MARKET_CACHE={shlex.quote(str(config.project_root / '.market-cache'))}",
        f"export BROKER_UNIVERSE={shlex.quote(str(config.project_root / 'universe.txt'))}",
        "unset BROKER_AS_OF",
    ]
    command = (
        f"exec {shlex.quote(sys.executable)} "
        f"{shlex.quote(str(broker_source.resolve()))} \"$@\""
    )
    if config.frozen_time:
        command += f" --as-of {shlex.quote(config.as_of.isoformat())}"
    launcher_lines.append(command)
    launcher_text = "\n".join(launcher_lines) + "\n"
    _write_text(launcher, launcher_text)
    launcher.chmod(0o755)
    return directory


def build_environment(config: RunConfig) -> dict[str, str]:
    directory = config.rollout_directory
    return {
        "BROKER_DATA_DIR": str(directory / ".broker"),
        "BROKER_MARKET_CACHE": str(config.project_root / ".market-cache"),
        "BROKER_UNIVERSE": str(config.project_root / "universe.txt"),
        # Mask inherited test overrides during real runs. Only explicit
        # --as-of tests freeze the time seen by Agent-issued broker commands.
        "BROKER_AS_OF": (
            config.as_of.isoformat() if config.frozen_time else ""
        ),
        "PYTHONUNBUFFERED": "1",
    }


def run_broker(
    workdir: Path,
    command: str,
    environment: Mapping[str, str],
    as_of: datetime,
    timeout_seconds: int,
) -> BrokerResult:
    arguments = [
        str(workdir / "broker"),
        command,
        "--json",
        "--as-of",
        as_of.isoformat(),
    ]
    try:
        completed = subprocess.run(
            arguments,
            text=True,
            capture_output=True,
            cwd=workdir,
            env={**os.environ, **environment},
            timeout=min(timeout_seconds, 120),
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise RunnerError(f"broker {command} timed out") from error
    try:
        document = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RunnerError(f"broker {command} returned invalid JSON") from error
    if not isinstance(document, dict):
        raise RunnerError(f"broker {command} did not return an object")
    result = BrokerResult(document, completed.stdout, completed.stderr, completed.returncode)
    if completed.returncode != 0 or document.get("ok") is not True:
        error = document.get("error", {})
        raise RunnerError(
            f"broker {command} failed: {error.get('code', 'UNKNOWN')} "
            f"{error.get('message', '')}".rstrip()
        )
    return result


def build_prompt(as_of: datetime, *, frozen_time: bool = False) -> str:
    local = as_of.astimezone(_NEW_YORK)
    test_notice = ""
    if frozen_time:
        test_notice = (
            "这是冻结时间的 smoke test。不得尝试联网搜索或获取当前真实时间之后的"
            "新闻、行情或其他信息；只能使用工作目录内允许的上下文和 ./broker。\n\n"
        )
    output_notice = (
        "本轮最终回复的第一行必须严格为：\n"
        f"## {local.isoformat()}\n"
        "不要把决策记录放进代码围栏。"
    )
    return (
        f"{FIXED_PROMPT}\n{test_notice}{output_notice}\n\n"
        f"当前时间：{local.isoformat()}。继续。\n"
    )


def validate_decision_record(
    response: str,
    as_of: datetime,
    *,
    frozen_time: bool = True,
    completed_at: datetime | None = None,
) -> str:
    raw = response.strip()
    expected = f"## {as_of.astimezone(_NEW_YORK).isoformat()}"
    if not raw:
        raise RunnerError("Agent returned an empty final response")
    if "```" in raw:
        raise RunnerError("decision record must not be wrapped in a code fence")
    required = (
        "### 本轮判断",
        "### 资金与持仓检查",
        "### 本轮操作",
        "### 后续计划",
    )
    headings = list(re.finditer(r"(?m)^## .+$", raw))
    if not headings:
        # The runner owns the authoritative timestamp. Recover only the narrow
        # formatting error where the response is otherwise exactly one complete
        # decision body beginning with the first required section. Do not turn
        # arbitrary prose, partial records, or duplicated sections into a record.
        complete_body = raw.startswith(required[0] + "\n") and all(
            len(re.findall(rf"(?m)^{re.escape(section)}$", raw)) == 1
            for section in required
        )
        if not complete_body:
            raise RunnerError("Agent must return exactly one decision record")
        record = f"{expected}\n\n{raw}"
    elif len(headings) != 1:
        raise RunnerError("Agent must return exactly one decision record")
    else:
        heading = headings[0]
        reported_heading = heading.group(0)
        try:
            reported_at = datetime.fromisoformat(
                reported_heading.removeprefix("## ")
            )
        except ValueError as error:
            raise RunnerError(
                "decision record timestamp must be valid ISO 8601"
            ) from error
        if reported_at.tzinfo is None or reported_at.utcoffset() is None:
            raise RunnerError("decision record timestamp must include a UTC offset")

        # The model-provided timestamp is presentation data, not an authority for
        # broker time. Resumed native sessions can retain a prompt from a failed
        # turn and repeat its stale timestamp. Always persist the runner's as_of so
        # every harness receives identical treatment and a harmless stale heading
        # cannot orphan an otherwise valid broker operation.
        record = raw[heading.start():].strip()
        if not record.startswith(reported_heading + "\n"):
            raise RunnerError(
                "decision record timestamp must be followed by a newline"
            )
        if reported_heading != expected:
            record = expected + record[len(reported_heading):]
    if "### 后续计划" not in record:
        # Preserve a semantically complete record when a model makes the
        # narrow formatting mistake observed in pilot: it emits the required
        # final section as a list label instead of a level-three heading.
        record = re.sub(
            r"(?m)^-\s*后续计划[：:]\s*$",
            "### 后续计划",
            record,
            count=1,
        )
    missing = [heading for heading in required if heading not in record]
    if missing:
        raise RunnerError(f"decision record is missing: {', '.join(missing)}")
    if not any(value in record for value in ("提交交易方案", "撤销交易方案", "不操作")):
        raise RunnerError("decision record does not describe an operation")
    return record


def append_decision(path: Path, record: str) -> None:
    existing = path.read_bytes()
    separator = b"" if existing.endswith(b"\n\n") else b"\n"
    _atomic_write(path, existing + separator + record.encode("utf-8") + b"\n")


def _client_for(harness: str) -> AgentClient:
    if harness == "codex":
        return CodexClient()
    if harness == "claude":
        return ClaudeClient()
    if harness == "dsh":
        return DshClient()
    if harness == "zcode":
        return ZCodeClient()
    raise ValueError(f"unsupported harness: {harness}")


def _json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


@contextmanager
def _rollout_lock(workdir: Path) -> Iterator[None]:
    lock_path = workdir / ".runner" / "run.lock"
    with lock_path.open("a+", encoding="utf-8") as stream:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RunnerError(f"rollout is already running: {workdir.name}") from error
        acquired_at = datetime.now(timezone.utc).isoformat()
        stream.seek(0)
        stream.truncate()
        stream.write(_json_text({"pid": os.getpid(), "acquired_at": acquired_at}))
        stream.flush()
        os.fsync(stream.fileno())
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _valid_session_id(harness: str, session_id: str) -> bool:
    if harness in {"codex", "claude"}:
        try:
            uuid.UUID(session_id)
        except ValueError:
            return False
        return True
    if harness == "dsh":
        return session_id.startswith("session-") and len(session_id) > len("session-")
    if harness == "zcode":
        return session_id.startswith("sess_") and len(session_id) > len("sess_")
    return False


def _load_session(path: Path, config: RunConfig) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RunnerError(f"invalid session file: {path}") from error
    if not isinstance(document, dict):
        raise RunnerError(f"invalid session file: {path}")
    if document.get("harness") != config.harness:
        raise RunnerError("rollout session harness does not match requested harness")
    if document.get("model") != config.model:
        raise RunnerError("rollout session model does not match requested model")
    session_id = document.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        raise RunnerError("rollout session_id is missing")
    if not _valid_session_id(config.harness, session_id):
        raise RunnerError(f"rollout {config.harness} session_id is invalid")
    return document


def _save_session(path: Path, config: RunConfig, session_id: str, previous: dict[str, Any] | None, run_id: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    document = {
        "session_id": session_id,
        "harness": config.harness,
        "model": config.model,
        "created_at": previous.get("created_at", now) if previous else now,
        "updated_at": now,
        "last_run_id": run_id,
    }
    _write_text(path, _json_text(document))


def _restore_snapshot(path: Path, before: bytes | None) -> None:
    if before is None:
        if path.exists():
            path.unlink()
    else:
        _atomic_write(path, before)


def _snapshot_paths(paths: tuple[Path, ...]) -> dict[Path, bytes | None]:
    return {
        path: path.read_bytes() if path.is_file() else None
        for path in paths
    }


def _restore_paths(snapshot: Mapping[Path, bytes | None]) -> list[str]:
    restored = []
    for path, before in snapshot.items():
        _restore_snapshot(path, before)
        restored.append(path.name)
    return restored


def run_once(
    config: RunConfig,
    *,
    agent_client: AgentClient | None = None,
    broker_call: BrokerCall = run_broker,
) -> dict[str, Any]:
    workdir = config.rollout_directory
    (workdir / ".runner").mkdir(parents=True, exist_ok=True)
    with _rollout_lock(workdir):
        initialize_rollout(config)
        return _run_once_locked(
            config,
            agent_client=agent_client,
            broker_call=broker_call,
        )


def _run_once_locked(
    config: RunConfig,
    *,
    agent_client: AgentClient | None = None,
    broker_call: BrokerCall = run_broker,
) -> dict[str, Any]:
    workdir = config.rollout_directory
    environment = build_environment(config)
    client = agent_client or _client_for(config.harness)
    session_path = workdir / ".runner" / "session.json"
    session_document = _load_session(session_path, config)
    session_id = session_document["session_id"] if session_document else None
    started_at = datetime.now(timezone.utc)
    run_id = started_at.strftime("%Y%m%dT%H%M%S.%fZ") + "-" + uuid.uuid4().hex[:8]
    log_directory = workdir / ".runner" / "logs" / run_id
    log_directory.mkdir(parents=True)
    prompt = build_prompt(config.as_of, frozen_time=config.frozen_time)
    metadata = {
        "run_id": run_id,
        "rollout_id": config.rollout_id,
        "harness": config.harness,
        "harness_version": client.version(),
        "model": config.model,
        "reasoning_effort": config.reasoning_effort,
        "session_id": session_id,
        "codex_session_id": session_id if config.harness == "codex" else None,
        "session_resumed": session_id is not None,
        "search_enabled": not config.frozen_time,
        "as_of": config.as_of.astimezone(_NEW_YORK).isoformat(),
        "timeout_seconds": config.timeout_seconds,
        "started_at": started_at.isoformat(),
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
    }
    _write_text(log_directory / "metadata.json", _json_text(metadata))
    _write_text(log_directory / "prompt.txt", prompt)

    decisions_path = workdir / "DECISIONS.md"
    broker_path = workdir / "broker"
    rule_paths = tuple(
        workdir / name
        for name in ("BROKER.md", "universe.txt", "DECISION_FORMAT.md")
    )
    decisions_before = decisions_path.read_bytes()
    broker_before = broker_path.read_bytes()
    rules_before = {path: path.read_bytes() for path in rule_paths}
    session_before = session_path.read_bytes() if session_path.exists() else None
    broker_transaction_snapshot: dict[Path, bytes | None] | None = None
    try:
        settled = broker_call(workdir, "settle", environment, config.as_of, config.timeout_seconds)
        _write_text(log_directory / "settle.json", _json_text(settled.document))
        pre_status = broker_call(workdir, "status", environment, config.as_of, config.timeout_seconds)
        _write_text(log_directory / "pre_status.json", _json_text(pre_status.document))

        # Settlement belongs to the completed market window and must survive
        # an Agent failure. Snapshot immediately afterwards so only mutations
        # made during this Agent turn are rolled back.
        broker_transaction_snapshot = _snapshot_paths((
            workdir / ".broker" / "state.json",
            workdir / ".broker" / "ledger.jsonl",
        ))

        try:
            agent_result = client.invoke(
                prompt=prompt,
                workdir=workdir,
                model=config.model,
                reasoning_effort=config.reasoning_effort,
                session_id=session_id,
                allow_search=not config.frozen_time,
                environment=environment,
                timeout_seconds=config.timeout_seconds,
                output_directory=log_directory,
            )
        except subprocess.TimeoutExpired as error:
            stdout = error.stdout or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            stderr = error.stderr or ""
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
            _write_text(log_directory / "agent_stdout.log", stdout)
            _write_text(log_directory / "agent_stderr.log", stderr)
            timed_out_session_id = (
                session_id_from_output(config.harness, stdout) or session_id
            )
            if (
                timed_out_session_id is not None
                and (session_id is None or timed_out_session_id == session_id)
            ):
                _save_session(
                    session_path, config, timed_out_session_id, session_document, run_id
                )
                session_id = timed_out_session_id
            raise RunnerError(
                f"{config.harness} exceeded {config.timeout_seconds} seconds"
            ) from error
        _write_text(log_directory / "agent_stdout.log", agent_result.stdout)
        _write_text(log_directory / "agent_stderr.log", agent_result.stderr)
        _write_text(log_directory / "agent_final.md", agent_result.final_response)
        _write_text(
            log_directory / "agent_result.json",
            _json_text({
                "command": list(agent_result.command),
                "returncode": agent_result.returncode,
                "duration_seconds": agent_result.duration_seconds,
                "session_id": agent_result.session_id,
                "session_resumed": session_document is not None,
            }),
        )

        integrity_errors = []
        current_decisions = (
            decisions_path.read_bytes() if decisions_path.is_file() else None
        )
        if current_decisions != decisions_before:
            _atomic_write(decisions_path, decisions_before)
            integrity_errors.append(
                "Agent modified DECISIONS.md; original history was restored"
            )
        current_broker = broker_path.read_bytes() if broker_path.is_file() else None
        if current_broker != broker_before:
            _atomic_write(broker_path, broker_before)
            broker_path.chmod(0o755)
            integrity_errors.append("Agent modified broker; launcher was restored")
        for path, before in rules_before.items():
            current = path.read_bytes() if path.is_file() else None
            if current != before:
                _atomic_write(path, before)
                path.chmod(0o444)
                integrity_errors.append(
                    f"Agent modified {path.name}; rule snapshot was restored"
                )

        current_session = session_path.read_bytes() if session_path.exists() else None
        if current_session != session_before:
            _restore_snapshot(session_path, session_before)
            integrity_errors.append("Agent modified .runner/session.json; it was restored")

        reported_session_id = agent_result.session_id
        if reported_session_id is None:
            integrity_errors.append(f"{config.harness} did not report a session ID")
        elif not _valid_session_id(config.harness, reported_session_id):
            integrity_errors.append(f"{config.harness} reported an invalid session ID")
        elif session_id is not None and reported_session_id != session_id:
            integrity_errors.append(
                f"{config.harness} resumed an unexpected session ID"
            )
        else:
            _save_session(
                session_path, config, reported_session_id, session_document, run_id
            )
            session_id = reported_session_id

        post_as_of = (
            config.as_of
            if config.frozen_time
            else datetime.now(_NEW_YORK)
        )
        post_status = broker_call(
            workdir, "status", environment, post_as_of, config.timeout_seconds
        )
        _write_text(log_directory / "post_status.json", _json_text(post_status.document))

        if agent_result.returncode != 0:
            stderr_lines = [
                line.strip()
                for line in agent_result.stderr.splitlines()
                if line.strip()
            ]
            detail = " | ".join(stderr_lines[-3:])
            suffix = f": {detail[:500]}" if detail else ""
            raise RunnerError(
                f"{config.harness} exited with code {agent_result.returncode}{suffix}"
            )
        if integrity_errors:
            raise RunnerError("; ".join(integrity_errors))
        record = validate_decision_record(
            agent_result.final_response,
            config.as_of,
            frozen_time=config.frozen_time,
            completed_at=post_as_of,
        )
        append_decision(decisions_path, record)
        completed_at = datetime.now(timezone.utc)
        summary = {
            "ok": True,
            "run_id": run_id,
            "rollout_id": config.rollout_id,
            "harness": config.harness,
            "model": config.model,
            "reasoning_effort": config.reasoning_effort,
            "session_id": session_id,
            "codex_session_id": session_id if config.harness == "codex" else None,
            "session_resumed": session_document is not None,
            "as_of": config.as_of.astimezone(_NEW_YORK).isoformat(),
            "duration_seconds": (completed_at - started_at).total_seconds(),
            "log_directory": str(log_directory),
            "settled": settled.document.get("settled", False),
            "fills": settled.document.get("fills", []),
            "post_status": post_status.document,
        }
        _write_text(log_directory / "summary.json", _json_text(summary))
        return summary
    except Exception as error:
        restored_broker_files: list[str] = []
        rollback_errors: list[str] = []
        if broker_transaction_snapshot is not None:
            try:
                restored_broker_files = _restore_paths(broker_transaction_snapshot)
            except OSError as rollback_error:
                rollback_errors.append(f"broker rollback failed: {rollback_error}")
            try:
                _atomic_write(decisions_path, decisions_before)
            except OSError as rollback_error:
                rollback_errors.append(f"decision rollback failed: {rollback_error}")
        failure = {
            "ok": False,
            "run_id": run_id,
            "rollout_id": config.rollout_id,
            "session_id": session_id,
            "codex_session_id": session_id if config.harness == "codex" else None,
            "error_type": type(error).__name__,
            "error": str(error),
            "broker_rolled_back": bool(
                broker_transaction_snapshot is not None and not rollback_errors
            ),
            "restored_broker_files": restored_broker_files,
            "rollback_errors": rollback_errors,
            "failed_at": datetime.now(timezone.utc).isoformat(),
        }
        _write_text(log_directory / "failure.json", _json_text(failure))
        raise
