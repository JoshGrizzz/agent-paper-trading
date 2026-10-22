"""Append-only JSON Lines audit ledger."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable


class LedgerCorruptError(RuntimeError):
    pass


class Ledger:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def read_all(self) -> tuple[dict[str, Any], ...]:
        if not self.path.exists():
            return ()
        events: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.endswith("\n"):
                    raise LedgerCorruptError(
                        f"ledger line {line_number} is not newline-terminated"
                    )
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as error:
                    raise LedgerCorruptError(
                        f"invalid ledger JSON on line {line_number}"
                    ) from error
                if not isinstance(value, dict) or not isinstance(
                    value.get("event_id"), str
                ):
                    raise LedgerCorruptError(
                        f"ledger line {line_number} has no valid event_id"
                    )
                events.append(value)
        return tuple(events)

    def append_missing(self, events: Iterable[dict[str, Any]]) -> None:
        pending = tuple(events)
        if not pending:
            return
        existing_ids = {event["event_id"] for event in self.read_all()}
        new_events = [
            event for event in pending if event["event_id"] not in existing_ids
        ]
        if not new_events:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            for event in new_events:
                handle.write(
                    json.dumps(
                        event,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    )
                    + "\n"
                )
            handle.flush()
            os.fsync(handle.fileno())
