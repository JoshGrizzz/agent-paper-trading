"""Prepare an isolated 15-rollout Claude V2 smoke cohort."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import shutil
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator
from zoneinfo import ZoneInfo

from trading_broker.state_store import StateStore

from .claude_successors import rollout_pairs
from .rollout_profile import load_profile, profile_document, profile_path
from .runner import RunConfig, RunnerError, _atomic_write, _json_text, initialize_rollout


_NEW_YORK = ZoneInfo("America/New_York")
_SET_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,23}$")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prepare_claude_v2_smoke")
    parser.add_argument("--source-set", default="official_claude_v2")
    parser.add_argument("--target-set", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--rollouts-root")
    return parser


@contextmanager
def _smoke_lock(rollouts_root: Path) -> Iterator[None]:
    path = rollouts_root / ".claude-v2-smoke.lock"
    with path.open("a+", encoding="utf-8") as stream:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RunnerError("another Claude V2 smoke preparation is running") from error
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _rows(
    *, rollouts_root: Path, source_set: str, target_set: str
) -> list[dict[str, Any]]:
    if not _SET_NAME.fullmatch(source_set) or not _SET_NAME.fullmatch(target_set):
        raise RunnerError("cohort names must use 1-24 letters, numbers, _ or -")
    if not target_set.startswith("adapter_smoke_"):
        raise RunnerError("smoke target set must start with adapter_smoke_")
    if source_set == target_set:
        raise RunnerError("source and target sets must differ")

    rows: list[dict[str, Any]] = []
    for source_id, target_id, model in rollout_pairs(source_set, target_set):
        if len(target_id) > 64:
            raise RunnerError(f"derived rollout ID exceeds 64 characters: {target_id}")
        source = rollouts_root / source_id
        target = rollouts_root / target_id
        if target.exists():
            raise RunnerError(f"smoke target already exists: {target_id}")
        if not (source / ".broker" / "state.json").is_file():
            raise RunnerError(f"missing source rollout: {source_id}")
        profile = load_profile(source)
        state = StateStore(source / ".broker").load()
        if state.initial_cash != profile.initial_cash:
            raise RunnerError(f"source initial cash mismatch: {source_id}")
        if state.positions or state.open_plan is not None:
            raise RunnerError(f"source rollout is not a clean cash account: {source_id}")
        if state.cash_total != profile.initial_cash:
            raise RunnerError(f"source cash changed before smoke preparation: {source_id}")
        if (source / ".runner" / "session.json").exists():
            raise RunnerError(f"source rollout already has an Agent session: {source_id}")
        rows.append({
            "source": source_id,
            "smoke": target_id,
            "model": model,
            "initial_cash": str(profile.initial_cash),
        })
    return rows


def prepare(
    *,
    project_root: Path,
    rollouts_root: Path,
    source_set: str,
    target_set: str,
    execute: bool,
) -> dict[str, Any]:
    captured_at = datetime.now(_NEW_YORK)
    rows = _rows(
        rollouts_root=rollouts_root,
        source_set=source_set,
        target_set=target_set,
    )
    if not execute:
        return {
            "ok": True,
            "mode": "preview",
            "mutated": False,
            "source_set": source_set,
            "target_set": target_set,
            "captured_at": captured_at.isoformat(),
            "rollouts": rows,
        }

    staging_root = rollouts_root / f".smoke-{target_set}-{uuid.uuid4().hex}"
    moved: list[Path] = []
    with _smoke_lock(rollouts_root):
        rows = _rows(
            rollouts_root=rollouts_root,
            source_set=source_set,
            target_set=target_set,
        )
        try:
            staging_root.mkdir(mode=0o700)
            for row in rows:
                staged = staging_root / row["smoke"]
                (staged / ".runner").mkdir(parents=True)
                document = profile_document(
                    initial_cash=load_profile(
                        rollouts_root / row["source"]
                    ).initial_cash,
                    cohort=target_set,
                    predecessor=row["source"],
                    overnight_smoke_until_next_noon=True,
                )
                _atomic_write(
                    profile_path(staged),
                    _json_text(document).encode("utf-8"),
                )
                config = RunConfig(
                    row["smoke"],
                    "claude",
                    row["model"],
                    captured_at,
                    project_root=project_root,
                    rollouts_root=staging_root,
                )
                initialize_rollout(config)
                StateStore(staged / ".broker").initialize(
                    load_profile(staged).initial_cash,
                    occurred_at=captured_at,
                )
                _atomic_write(
                    staged / ".runner" / "SMOKE.json",
                    _json_text({
                        "schema_version": 1,
                        "source": row["source"],
                        "target_set": target_set,
                        "created_at": captured_at.isoformat(),
                        "disposable": True,
                    }).encode("utf-8"),
                )

            for row in rows:
                staged = staging_root / row["smoke"]
                target = rollouts_root / row["smoke"]
                os.replace(staged, target)
                moved.append(target)
        except Exception:
            for target in reversed(moved):
                shutil.rmtree(target, ignore_errors=True)
            raise
        finally:
            shutil.rmtree(staging_root, ignore_errors=True)

    return {
        "ok": True,
        "mode": "execute",
        "mutated": True,
        "source_set": source_set,
        "target_set": target_set,
        "created_at": captured_at.isoformat(),
        "rollouts": rows,
    }


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    project_root = Path(__file__).resolve().parents[2]
    rollouts_root = (
        Path(arguments.rollouts_root).resolve()
        if arguments.rollouts_root
        else project_root / "rollouts"
    )
    try:
        result = prepare(
            project_root=project_root,
            rollouts_root=rollouts_root,
            source_set=arguments.source_set,
            target_set=arguments.target_set,
            execute=arguments.execute,
        )
    except (OSError, ValueError, RunnerError) as error:
        print(json.dumps({
            "ok": False,
            "error": {"type": type(error).__name__, "message": str(error)},
        }, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
