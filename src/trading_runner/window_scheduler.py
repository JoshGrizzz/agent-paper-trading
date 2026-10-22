"""Five-wave decision-window scheduler for the formal experiment."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from .agent_client import ClaudeClient, CodexClient, ZCodeClient


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WAVE_COUNT = 5
MODEL_CONFIGS = {
    "codex": (
        "gpt-5.6-sol",
        "gpt-5.6-luna",
        "gpt-6-sol",
        "gpt-6-luna",
        "gpt-6-astra",
    ),
    "claude": ("opus", "sonnet", "haiku"),
    "zcode": ("GLM-5.3",),
}
CLIENT_TYPES = {
    "codex": CodexClient,
    "claude": ClaudeClient,
    "zcode": ZCodeClient,
}


@dataclass(frozen=True, slots=True)
class WorkerSpec:
    wave: int
    rollout_number: int
    model_index: int
    model: str
    rollout_id: str
    command: tuple[str, ...]
    log_path: Path
    conversation: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_decision_window",
        description=(
            "Run one formal decision window as five sequential waves. Each wave "
            "runs one rollout for every model configuration concurrently."
        ),
    )
    parser.add_argument(
        "--harness",
        required=True,
        choices=tuple(MODEL_CONFIGS),
        help=(
            "Provider group to run: codex (5-wide), claude (3-wide), "
            "or zcode (1-wide)."
        ),
    )
    parser.add_argument(
        "--rollout-set",
        required=True,
        help="Stable namespace shared by all five repetitions of each model.",
    )
    parser.add_argument(
        "--window-index",
        required=True,
        type=int,
        help="One-based global decision-window number; controls five-wave rotation.",
    )
    parser.add_argument(
        "--models",
        help="Comma-separated model labels; must match the harness concurrency exactly.",
    )
    parser.add_argument(
        "--reasoning-effort",
        default="high",
        choices=("low", "medium", "high", "xhigh", "max"),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=900,
        help="Per-agent timeout passed to run_rollout (default: 900 seconds).",
    )
    parser.add_argument(
        "--as-of",
        help=(
            "Optional ISO 8601 frozen test time with UTC offset. Omit for a live "
            "decision window."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print all five waves without creating state or starting agents.",
    )
    return parser


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_")
    return (slug or "model")[:20]


def resolve_models(harness: str, supplied: str | None) -> tuple[str, ...]:
    expected = len(MODEL_CONFIGS[harness])
    if supplied is None:
        return MODEL_CONFIGS[harness]
    models = tuple(item.strip() for item in supplied.split(","))
    if any(not item for item in models):
        raise ValueError("--models contains an empty model label")
    if len(models) != expected:
        raise ValueError(
            f"--models must contain exactly {expected} labels for {harness}"
        )
    if len(set(models)) != len(models):
        raise ValueError("--models must identify distinct model configurations")
    return models


def parse_as_of(value: str | None) -> str | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("--as-of must include a UTC offset")
    return parsed.isoformat()


def rollout_order(window_index: int) -> tuple[int, ...]:
    if window_index <= 0:
        raise ValueError("--window-index must be a positive integer")
    first = (window_index - 1) % WAVE_COUNT
    return tuple(((first + offset) % WAVE_COUNT) + 1 for offset in range(WAVE_COUNT))


def build_wave_specs(
    *,
    harness: str,
    rollout_set: str,
    window_index: int,
    models: Sequence[str],
    reasoning_effort: str,
    timeout: int,
    as_of: str | None,
    batch_directory: Path,
    project_root: Path = PROJECT_ROOT,
    python_executable: str = sys.executable,
) -> list[list[WorkerSpec]]:
    waves: list[list[WorkerSpec]] = []
    for wave, rollout_number in enumerate(rollout_order(window_index), start=1):
        wave_specs: list[WorkerSpec] = []
        wave_directory = batch_directory / f"wave_{wave:02d}_r{rollout_number:02d}"
        for model_index, model in enumerate(models, start=1):
            slug = safe_slug(model)
            rollout_id = (
                f"{rollout_set}_{model_index}_{slug}_r{rollout_number:02d}"
            )
            if len(rollout_id) > 64:
                raise ValueError(
                    f"derived rollout ID exceeds 64 characters: {rollout_id}"
                )
            log_path = wave_directory / f"{model_index:02d}_{slug}.log"
            session_path = (
                project_root / "rollouts" / rollout_id / ".runner" / "session.json"
            )
            command = [
                python_executable,
                str(project_root / "run_rollout"),
                "run",
                "--rollout",
                rollout_id,
                "--harness",
                harness,
                "--model",
                model,
                "--reasoning-effort",
                reasoning_effort,
                "--timeout",
                str(timeout),
            ]
            if as_of is not None:
                command.extend(("--as-of", as_of))
            wave_specs.append(
                WorkerSpec(
                    wave=wave,
                    rollout_number=rollout_number,
                    model_index=model_index,
                    model=model,
                    rollout_id=rollout_id,
                    command=tuple(command),
                    log_path=log_path,
                    conversation="resume" if session_path.is_file() else "new",
                )
            )
        waves.append(wave_specs)
    return waves


def load_result_document(log_path: Path) -> dict[str, Any] | None:
    if not log_path.is_file():
        return None
    for line in reversed(
        log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    ):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def stop_process_group(process: subprocess.Popen[Any], *, force: bool = False) -> None:
    if process.poll() is not None:
        return
    signum = signal.SIGKILL if force else signal.SIGTERM
    try:
        os.killpg(process.pid, signum)
    except ProcessLookupError:
        return


def _run_wave(
    specs: Sequence[WorkerSpec],
    *,
    timeout: int,
) -> tuple[list[dict[str, Any]], bool]:
    workers: list[dict[str, Any]] = []
    try:
        for spec in specs:
            spec.log_path.parent.mkdir(parents=True, exist_ok=True)
            log_stream = spec.log_path.open("w", encoding="utf-8")
            try:
                process = subprocess.Popen(
                    spec.command,
                    cwd=PROJECT_ROOT,
                    stdout=log_stream,
                    stderr=subprocess.STDOUT,
                    text=True,
                    start_new_session=True,
                )
            except BaseException:
                log_stream.close()
                raise
            workers.append(
                {
                    "spec": spec,
                    "log_stream": log_stream,
                    "process": process,
                    "started_at": datetime.now(timezone.utc),
                    "started_monotonic": time.monotonic(),
                    "finished_at": None,
                    "outer_timed_out": False,
                }
            )

        pending = set(range(len(workers)))
        # The formal protocol caps the whole wave, rather than granting each
        # child an additional grace period after its own timeout.
        outer_timeout = timeout
        while pending:
            for worker_index in list(pending):
                worker = workers[worker_index]
                process = worker["process"]
                returncode = process.poll()
                elapsed = time.monotonic() - worker["started_monotonic"]
                if returncode is None and elapsed > outer_timeout:
                    worker["outer_timed_out"] = True
                    stop_process_group(process)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        stop_process_group(process, force=True)
                        process.wait()
                    returncode = process.returncode
                if returncode is None:
                    continue

                worker["finished_at"] = datetime.now(timezone.utc)
                worker["log_stream"].close()
                pending.remove(worker_index)
                document = load_result_document(worker["spec"].log_path)
                worker["document"] = document
                worker["returncode"] = returncode
                worker["passed"] = (
                    returncode == 0
                    and document is not None
                    and document.get("ok") is True
                )
            if pending:
                time.sleep(0.1)
    except BaseException:
        for worker in workers:
            stop_process_group(worker["process"])
        deadline = time.monotonic() + 5
        for worker in workers:
            remaining = max(0.0, deadline - time.monotonic())
            try:
                worker["process"].wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                stop_process_group(worker["process"], force=True)
        for worker in workers:
            worker["process"].wait()
            if not worker["log_stream"].closed:
                worker["log_stream"].close()
        raise
    finally:
        for worker in workers:
            if not worker["log_stream"].closed:
                worker["log_stream"].close()

    results: list[dict[str, Any]] = []
    for worker in sorted(workers, key=lambda item: item["spec"].model_index):
        spec = worker["spec"]
        document = worker.get("document")
        results.append(
            {
                "as_of": document.get("as_of") if document else None,
                "conversation": spec.conversation,
                "duration_seconds": (
                    worker["finished_at"] - worker["started_at"]
                ).total_seconds(),
                "error": (
                    document.get("error")
                    if document
                    else "missing runner JSON result"
                ),
                "fills": document.get("fills", []) if document else [],
                "log_path": str(spec.log_path),
                "model": spec.model,
                "model_index": spec.model_index,
                "ok": bool(worker["passed"]),
                "outer_timed_out": worker["outer_timed_out"],
                "returncode": worker["returncode"],
                "rollout_id": spec.rollout_id,
                "rollout_number": spec.rollout_number,
                "run_id": document.get("run_id") if document else None,
                "session_id": document.get("session_id") if document else None,
                "session_resumed": (
                    document.get("session_resumed") if document else None
                ),
                "settled": document.get("settled") if document else None,
                "wave": spec.wave,
            }
        )
    return results, all(item["ok"] for item in results)


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.timeout <= 0:
        raise SystemExit("--timeout must be a positive integer")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,23}", arguments.rollout_set):
        raise SystemExit(
            "--rollout-set must be 1-24 characters using letters, numbers, _ or -"
        )
    try:
        models = resolve_models(arguments.harness, arguments.models)
        as_of = parse_as_of(arguments.as_of)
        order = rollout_order(arguments.window_index)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    if not arguments.dry_run:
        if shutil.which(arguments.harness) is None:
            raise SystemExit(f"{arguments.harness} CLI was not found on PATH")
        dependency = subprocess.run(
            [sys.executable, "-c", "import yfinance"],
            text=True,
            capture_output=True,
            check=False,
        )
        if dependency.returncode != 0:
            raise SystemExit(
                "yfinance is unavailable; activate the finance environment first"
            )

    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    batch_id = (
        f"window_{arguments.harness}_w{arguments.window_index:04d}_{stamp}_{os.getpid()}"
    )
    batch_directory = PROJECT_ROOT / "parallel_runs" / batch_id
    try:
        waves = build_wave_specs(
            harness=arguments.harness,
            rollout_set=arguments.rollout_set,
            window_index=arguments.window_index,
            models=models,
            reasoning_effort=arguments.reasoning_effort,
            timeout=arguments.timeout,
            as_of=as_of,
            batch_directory=batch_directory,
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error

    harness_version = (
        "not checked (dry-run)"
        if arguments.dry_run
        else CLIENT_TYPES[arguments.harness]().version()
    )
    print(f"Decision-window batch: {batch_id}")
    print(f"Harness: {arguments.harness}")
    print(f"Harness version: {harness_version}")
    print(f"Persistent rollout set: {arguments.rollout_set}")
    print(f"Window index: {arguments.window_index}")
    print(f"Wave order: {', '.join(f'r{item:02d}' for item in order)}")
    print(f"Concurrency per wave: {len(models)}")
    print(f"Models: {', '.join(models)}")
    print(f"Reasoning effort: {arguments.reasoning_effort}")
    print(f"Per-agent timeout: {arguments.timeout} seconds")
    print("Broker time: live" if as_of is None else f"Frozen broker time: {as_of}")
    print(
        "WARNING: this is a five-wave paper-trading decision window. It may "
        "create or resume accounts and submit or cancel simulated orders."
    )

    for specs in waves:
        print(
            f"\nWave {specs[0].wave}/{WAVE_COUNT}: rollout "
            f"r{specs[0].rollout_number:02d} ({len(specs)} concurrent)"
        )
        for spec in specs:
            print(
                f"  [{spec.model_index}/{len(specs)}] model={spec.model} "
                f"rollout={spec.rollout_id} conversation={spec.conversation}"
            )
            print(f"  command: {shlex.join(spec.command)}")
            print(f"  log: {spec.log_path}")

    if arguments.dry_run:
        print(
            "\nDry run only: no directories, accounts, sessions, orders, or agents "
            "were created."
        )
        return 0

    batch_directory.mkdir(parents=True)
    started_at = datetime.now(timezone.utc)
    wave_summaries: list[dict[str, Any]] = []
    all_results: list[dict[str, Any]] = []
    try:
        for specs in waves:
            wave_started_at = datetime.now(timezone.utc)
            print(
                f"\nStarting wave {specs[0].wave}/{WAVE_COUNT} "
                f"(rollout r{specs[0].rollout_number:02d})..."
            )
            results, passed = _run_wave(specs, timeout=arguments.timeout)
            all_results.extend(results)
            passed_count = sum(bool(item["ok"]) for item in results)
            wave_summary = {
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "concurrency": len(specs),
                "failed": len(specs) - passed_count,
                "ok": passed,
                "passed": passed_count,
                "results": results,
                "rollout_number": specs[0].rollout_number,
                "started_at": wave_started_at.isoformat(),
                "wave": specs[0].wave,
            }
            wave_summaries.append(wave_summary)
            write_json(specs[0].log_path.parent / "summary.json", wave_summary)
            status = "PASS" if passed else "FAIL"
            print(
                f"Wave {specs[0].wave}/{WAVE_COUNT} {status}: "
                f"{passed_count}/{len(specs)} rollouts passed."
            )
            if not passed:
                print("Continuing only after this wave has fully stopped.")
    except KeyboardInterrupt:
        print("\nInterrupted; active wave was stopped. No later wave was started.", file=sys.stderr)
        return 130

    passed_count = sum(bool(item["ok"]) for item in all_results)
    summary = {
        "as_of": as_of,
        "batch_id": batch_id,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "concurrency_per_wave": len(models),
        "failed": len(all_results) - passed_count,
        "harness": arguments.harness,
        "harness_version": harness_version,
        "models": list(models),
        "ok": passed_count == len(all_results),
        "passed": passed_count,
        "reasoning_effort": arguments.reasoning_effort,
        "results": all_results,
        "rollout_set": arguments.rollout_set,
        "started_at": started_at.isoformat(),
        "timeout_seconds": arguments.timeout,
        "total_rollouts": len(all_results),
        "wave_count": WAVE_COUNT,
        "wave_order": list(order),
        "waves": wave_summaries,
        "window_index": arguments.window_index,
    }
    summary_path = batch_directory / "summary.json"
    write_json(summary_path, summary)
    print(
        f"\nDecision window result: {passed_count}/{len(all_results)} rollouts "
        f"passed. Summary: {summary_path}"
    )
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
