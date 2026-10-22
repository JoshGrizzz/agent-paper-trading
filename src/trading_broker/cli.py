"""Command-line interface for the deterministic paper broker."""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .market_data import YahooFinanceProvider
from .plan_io import PlanInputError, load_plan_file
from .service import BrokerService, ServiceError
from .state_store import StateConflictError
from .validator import PlanValidationError


_NEW_YORK = ZoneInfo("America/New_York")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="broker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("status", "settle"):
        command = subparsers.add_parser(name)
        command.add_argument("--json", action="store_true")
        command.add_argument("--as-of", help=argparse.SUPPRESS)

    submit = subparsers.add_parser("submit-plan")
    submit.add_argument("--file", required=True)
    submit.add_argument("--json", action="store_true")
    submit.add_argument("--as-of", help=argparse.SUPPRESS)

    cancel = subparsers.add_parser("cancel")
    cancel.add_argument("plan_id")
    cancel.add_argument("--json", action="store_true")
    cancel.add_argument("--as-of", help=argparse.SUPPRESS)
    return parser


def _as_of(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("--as-of must include a UTC offset")
    return parsed


def _service() -> BrokerService:
    repository = Path(__file__).resolve().parents[2]
    data_directory = Path(os.environ.get("BROKER_DATA_DIR", Path.cwd()))
    cache_directory = Path(
        os.environ.get("BROKER_MARKET_CACHE", repository / ".market-cache")
    )
    universe_path = Path(
        os.environ.get("BROKER_UNIVERSE", repository / "universe.txt")
    )
    return BrokerService.from_paths(
        data_directory,
        cache_directory,
        universe_path,
        YahooFinanceProvider(),
        clock=lambda: datetime.now(_NEW_YORK),
    )


def _error_document(command: str, error: Exception, now: datetime) -> dict:
    code = "INTERNAL_ERROR"
    message = "internal broker error"
    details = {}
    fills = []
    if isinstance(error, ServiceError):
        code = error.code
        message = error.message
        details = error.details
        from .service import fill_view

        fills = [fill_view(fill) for fill in error.fills]
    elif isinstance(error, PlanInputError):
        code = error.code.value
        message = str(error)
        details = {"path": error.path}
    elif isinstance(error, PlanValidationError):
        code = error.issue.code.value
        message = error.issue.message
        details = dict(error.issue.details)
    elif isinstance(error, StateConflictError):
        code = "STATE_CONFLICT"
        message = str(error)
    elif isinstance(error, (ValueError, FileNotFoundError)):
        code = "INVALID_ARGUMENT"
        message = str(error)
    return {
        "ok": False,
        "command": command,
        "as_of": now.isoformat(),
        "settled_through": None,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
        "fills": fills,
    }


def _is_public_error(error: Exception) -> bool:
    return isinstance(
        error,
        (
            ServiceError,
            PlanInputError,
            PlanValidationError,
            StateConflictError,
            ValueError,
            FileNotFoundError,
        ),
    )


def _write_internal_diagnostic(command: str, error: Exception, now: datetime) -> None:
    """Persist private diagnostics without changing the stable public error."""

    data_directory = Path(os.environ.get("BROKER_DATA_DIR", Path.cwd()))
    path = data_directory / "internal_errors.jsonl"
    document = {
        "occurred_at": now.isoformat(),
        "command": command,
        "error_type": type(error).__name__,
        "message": str(error),
        "traceback": "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        ),
    }
    try:
        data_directory.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(descriptor, "a", encoding="utf-8") as stream:
            stream.write(
                json.dumps(document, ensure_ascii=False, sort_keys=True) + "\n"
            )
    except Exception:
        # Diagnostic failure must not replace the original stable JSON response.
        pass


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    now = datetime.now(_NEW_YORK)
    try:
        as_of = _as_of(arguments.as_of or os.environ.get("BROKER_AS_OF"))
        service = _service()
        if arguments.command == "status":
            document = service.status(as_of=as_of)
        elif arguments.command == "settle":
            document = service.settle(as_of=as_of)
        elif arguments.command == "submit-plan":
            document = service.submit_plan(
                load_plan_file(arguments.file),
                as_of=as_of,
            )
        else:
            document = service.cancel(arguments.plan_id, as_of=as_of)
        exit_code = 0
    except Exception as error:
        if not _is_public_error(error):
            _write_internal_diagnostic(arguments.command, error, now)
        document = _error_document(arguments.command, error, now)
        exit_code = 2

    sys.stdout.write(
        json.dumps(document, ensure_ascii=False, sort_keys=True) + "\n"
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
