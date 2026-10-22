"""Command-line entry point for manual one-shot rollout execution."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .runner import RunConfig, initialize_rollout, run_once


_NEW_YORK = ZoneInfo("America/New_York")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run-rollout")
    subparsers = parser.add_subparsers(dest="command", required=True)

    initialize = subparsers.add_parser("init")
    initialize.add_argument("--rollout", required=True)
    initialize.add_argument("--rollouts-root")

    run = subparsers.add_parser("run")
    run.add_argument("--rollout", required=True)
    run.add_argument(
        "--harness",
        required=True,
        choices=("codex", "claude", "dsh", "zcode"),
    )
    run.add_argument("--model", required=True)
    run.add_argument(
        "--reasoning-effort",
        choices=("low", "medium", "high", "xhigh", "max"),
        default="medium",
    )
    run.add_argument("--as-of", help="ISO 8601 test time with a UTC offset")
    run.add_argument("--timeout", type=int, default=900)
    run.add_argument("--rollouts-root")
    return parser


def _as_of(value: str | None) -> datetime:
    if value is None:
        return datetime.now(_NEW_YORK)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("--as-of must include a UTC offset")
    return parsed.astimezone(_NEW_YORK)


def _config(arguments: argparse.Namespace, *, initialize: bool = False) -> RunConfig:
    return RunConfig(
        rollout_id=arguments.rollout,
        harness="codex" if initialize else arguments.harness,
        model="not-selected" if initialize else arguments.model,
        as_of=datetime.now(_NEW_YORK) if initialize else _as_of(arguments.as_of),
        timeout_seconds=900 if initialize else arguments.timeout,
        reasoning_effort=(
            "medium" if initialize else arguments.reasoning_effort
        ),
        rollouts_root=(
            Path(arguments.rollouts_root).resolve()
            if arguments.rollouts_root
            else None
        ),
        frozen_time=False if initialize else arguments.as_of is not None,
    )


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "init":
            config = _config(arguments, initialize=True)
            directory = initialize_rollout(config)
            result = {
                "ok": True,
                "command": "init",
                "rollout": config.rollout_id,
                "directory": str(directory),
            }
        else:
            result = run_once(_config(arguments))
        exit_code = 0
    except Exception as error:
        result = {
            "ok": False,
            "command": arguments.command,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
            },
        }
        exit_code = 2
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
