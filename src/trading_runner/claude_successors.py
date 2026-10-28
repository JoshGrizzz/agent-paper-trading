"""Transactional handoff from Claude V1 rollouts to clean V2 successors."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import shutil
import sys
import uuid
from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterator
from zoneinfo import ZoneInfo

from trading_broker.state_store import StateStore

from .rollout_profile import profile_document, profile_path
from .runner import (
    RunConfig,
    RunnerError,
    _atomic_write,
    _json_text,
    _rollout_lock,
    build_environment,
    initialize_rollout,
    run_broker,
)


_NEW_YORK = ZoneInfo("America/New_York")
_MODELS = ((1, "opus"), (2, "sonnet"), (3, "haiku"))
_WAVES = range(1, 6)


def rollout_pairs(source_set: str, target_set: str) -> tuple[tuple[str, str, str], ...]:
    pairs = []
    for model_index, model in _MODELS:
        for wave in _WAVES:
            suffix = f"{model_index}_{model}_r{wave:02d}"
            pairs.append((f"{source_set}_{suffix}", f"{target_set}_{suffix}", model))
    return tuple(pairs)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prepare_claude_successors")
    parser.add_argument("--source-set", default="official_claude")
    parser.add_argument("--target-set", default="official_claude_v2")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--as-of", help="ISO 8601 test time with UTC offset")
    parser.add_argument("--rollouts-root")
    return parser


def _as_of(value: str | None) -> datetime:
    if value is None:
        return datetime.now(_NEW_YORK)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("--as-of must include a UTC offset")
    return parsed.astimezone(_NEW_YORK)


def _state_checksum(directory: Path) -> str:
    digest = hashlib.sha256()
    for name in ("state.json", "ledger.jsonl"):
        path = directory / ".broker" / name
        if not path.is_file():
            raise RunnerError(f"missing predecessor broker file: {path}")
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _stored_equity(directory: Path) -> Decimal:
    state = StateStore(directory / ".broker").load()
    total = state.cash_total
    for position in state.positions:
        if position.latest_price is None:
            raise RunnerError(f"{directory.name} has a position without a valuation")
        total += position.latest_price * position.quantity
    return total


@contextmanager
def _global_lock(rollouts_root: Path) -> Iterator[None]:
    path = rollouts_root / ".claude-successor.lock"
    with path.open("a+", encoding="utf-8") as stream:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RunnerError("another Claude cohort handoff is running") from error
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _preflight(
    *, project_root: Path, rollouts_root: Path, source_set: str, target_set: str
) -> tuple[tuple[str, str, str], ...]:
    if source_set == target_set:
        raise RunnerError("source and target cohort names must differ")
    pairs = rollout_pairs(source_set, target_set)
    for source_id, target_id, _ in pairs:
        source = rollouts_root / source_id
        target = rollouts_root / target_id
        if not (source / ".broker" / "state.json").is_file():
            raise RunnerError(f"missing source rollout: {source_id}")
        if (source / ".runner" / "ARCHIVED.json").exists():
            raise RunnerError(f"source rollout is already archived: {source_id}")
        if target.exists():
            raise RunnerError(f"target rollout already exists: {target_id}")
    manifest = project_root / "cohorts" / f"{target_set}.json"
    if manifest.exists():
        raise RunnerError(f"cohort manifest already exists: {manifest}")
    return pairs


def preview(
    *, project_root: Path, rollouts_root: Path, source_set: str, target_set: str,
    as_of: datetime,
) -> dict[str, Any]:
    pairs = _preflight(
        project_root=project_root, rollouts_root=rollouts_root,
        source_set=source_set, target_set=target_set,
    )
    rows = []
    for source_id, target_id, model in pairs:
        directory = rollouts_root / source_id
        state = StateStore(directory / ".broker").load()
        rows.append({
            "predecessor": source_id,
            "successor": target_id,
            "model": model,
            "stored_equity_preview": str(_stored_equity(directory)),
            "has_open_plan": state.open_plan is not None,
            "state_checksum": _state_checksum(directory),
        })
    return {
        "ok": True, "mode": "preview", "mutated": False,
        "source_set": source_set, "target_set": target_set,
        "captured_as_of": as_of.isoformat(), "rollouts": rows,
        "warning": "Preview uses stored valuations; --execute performs synchronized settlement and refresh.",
    }


def execute(
    *, project_root: Path, rollouts_root: Path, source_set: str, target_set: str,
    as_of: datetime,
) -> dict[str, Any]:
    pairs = _preflight(
        project_root=project_root, rollouts_root=rollouts_root,
        source_set=source_set, target_set=target_set,
    )
    staging_root = rollouts_root / f".handoff-{target_set}-{uuid.uuid4().hex}"
    manifest_path = project_root / "cohorts" / f"{target_set}.json"
    moved_targets: list[Path] = []
    archive_paths: list[Path] = []
    manifest_written = False
    rows: list[dict[str, Any]] = []
    with _global_lock(rollouts_root):
        pairs = _preflight(
            project_root=project_root, rollouts_root=rollouts_root,
            source_set=source_set, target_set=target_set,
        )
        with ExitStack() as stack:
            for source_id, _, _ in sorted(pairs):
                stack.enter_context(_rollout_lock(rollouts_root / source_id))
            try:
                for source_id, target_id, model in pairs:
                    source = rollouts_root / source_id
                    source_config = RunConfig(
                        source_id, "claude", model, as_of,
                        project_root=project_root, rollouts_root=rollouts_root,
                        frozen_time=True,
                    )
                    environment = build_environment(source_config)
                    run_broker(source, "settle", environment, as_of, 900)
                    run_broker(source, "refresh-valuation", environment, as_of, 900)
                    status = run_broker(source, "status", environment, as_of, 900).document
                    if status.get("open_plans"):
                        raise RunnerError(f"{source_id} still has an unexpired open plan")
                    equity = Decimal(status["account"]["equity"])
                    if not equity.is_finite() or equity <= 0:
                        raise RunnerError(f"{source_id} has invalid final equity")
                    rows.append({
                        "predecessor": source_id, "successor": target_id,
                        "model": model, "handoff_as_of": as_of.isoformat(),
                        "predecessor_final_equity": str(equity),
                        "successor_initial_cash": str(equity),
                        "predecessor_state_checksum": _state_checksum(source),
                    })

                staging_root.mkdir(mode=0o700)
                for row in rows:
                    target_id = row["successor"]
                    staged = staging_root / target_id
                    (staged / ".runner").mkdir(parents=True)
                    equity = Decimal(row["successor_initial_cash"])
                    _atomic_write(
                        profile_path(staged),
                        _json_text(profile_document(
                            initial_cash=equity, cohort=target_set,
                            predecessor=row["predecessor"],
                        )).encode("utf-8"),
                    )
                    _atomic_write(
                        staged / ".runner" / "PENDING.json",
                        _json_text({"target_set": target_set, "as_of": as_of.isoformat()}).encode("utf-8"),
                    )
                    config = RunConfig(
                        target_id, "claude", row["model"], as_of,
                        project_root=project_root, rollouts_root=staging_root,
                        frozen_time=True,
                    )
                    initialize_rollout(config)
                    state = StateStore(staged / ".broker").initialize(
                        equity, occurred_at=as_of
                    )
                    if state.positions or state.open_plan is not None:
                        raise RunnerError(f"staged successor is not clean: {target_id}")
                    row["successor_state_checksum"] = _state_checksum(staged)
                    lineage = {"schema_version": 1, **row, "clean_restart": True}
                    _atomic_write(
                        staged / "LINEAGE.json",
                        _json_text(lineage).encode("utf-8"),
                    )

                for row in rows:
                    staged = staging_root / row["successor"]
                    target = rollouts_root / row["successor"]
                    os.replace(staged, target)
                    moved_targets.append(target)

                manifest = {
                    "schema_version": 1, "status": "committed",
                    "source_set": source_set, "target_set": target_set,
                    "handoff_as_of": as_of.isoformat(), "rollouts": rows,
                }
                _atomic_write(manifest_path, _json_text(manifest).encode("utf-8"))
                manifest_written = True
                archived_at = datetime.now(timezone.utc).isoformat()
                for row in rows:
                    archive_path = rollouts_root / row["predecessor"] / ".runner" / "ARCHIVED.json"
                    _atomic_write(archive_path, _json_text({
                        "schema_version": 1, "archived_at": archived_at,
                        "handoff_as_of": as_of.isoformat(),
                        "successor": row["successor"],
                        "manifest": str(manifest_path.relative_to(project_root)),
                    }).encode("utf-8"))
                    archive_paths.append(archive_path)
                for target in moved_targets:
                    (target / ".runner" / "PENDING.json").unlink()
            except Exception:
                for archive_path in archive_paths:
                    archive_path.unlink(missing_ok=True)
                if manifest_written:
                    manifest_path.unlink(missing_ok=True)
                for target in moved_targets:
                    shutil.rmtree(target, ignore_errors=True)
                raise
            finally:
                shutil.rmtree(staging_root, ignore_errors=True)
    return {
        "ok": True, "mode": "execute", "mutated": True,
        "source_set": source_set, "target_set": target_set,
        "handoff_as_of": as_of.isoformat(), "manifest": str(manifest_path),
        "rollouts": rows,
    }


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    project_root = Path(__file__).resolve().parents[2]
    rollouts_root = (
        Path(arguments.rollouts_root).resolve()
        if arguments.rollouts_root else project_root / "rollouts"
    )
    as_of = _as_of(arguments.as_of)
    try:
        result = (
            execute(
                project_root=project_root, rollouts_root=rollouts_root,
                source_set=arguments.source_set, target_set=arguments.target_set,
                as_of=as_of,
            ) if arguments.execute else preview(
                project_root=project_root, rollouts_root=rollouts_root,
                source_set=arguments.source_set, target_set=arguments.target_set,
                as_of=as_of,
            )
        )
        exit_code = 0
    except Exception as error:
        result = {"ok": False, "mode": "execute" if arguments.execute else "preview", "error": {"type": type(error).__name__, "message": str(error)}}
        exit_code = 2
    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
