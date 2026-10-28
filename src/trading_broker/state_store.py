"""Atomic state snapshots with ledger-backed crash recovery."""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
import uuid
from contextlib import contextmanager
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Iterator

from .ledger import Ledger
from .models import CandidateName, CandidatePlan, LimitOrder, Side, TradePlan
from .state_models import (
    BrokerState,
    DailyDirection,
    PositionReservation,
    PositionState,
    StoredOpenPlan,
    initial_state,
)


class StateConflictError(RuntimeError):
    pass


class StateCorruptError(RuntimeError):
    pass


class InitialCashMismatchError(RuntimeError):
    pass


def _candidate_to_dict(candidate: CandidatePlan) -> dict[str, Any]:
    return {
        "name": candidate.name.value,
        "accepted": candidate.accepted,
        "rejection_reason": candidate.rejection_reason,
        "orders": [
            {
                "order_id": order.order_id,
                "symbol": order.symbol,
                "side": order.side.value,
                "quantity": order.quantity,
                "limit_price": str(order.limit_price),
            }
            for order in candidate.orders
        ],
    }


def _candidate_from_dict(value: dict[str, Any]) -> CandidatePlan:
    return CandidatePlan(
        name=CandidateName(value["name"]),
        orders=tuple(
            LimitOrder(
                order_id=item["order_id"],
                symbol=item["symbol"],
                side=Side(item["side"]),
                quantity=item["quantity"],
                limit_price=Decimal(item["limit_price"]),
            )
            for item in value["orders"]
        ),
        accepted=value["accepted"],
        rejection_reason=value.get("rejection_reason"),
    )


def _plan_to_dict(plan: TradePlan) -> dict[str, Any]:
    return {
        "plan_id": plan.plan_id,
        "decision_at": plan.decision_at.isoformat(),
        "valid_from": plan.valid_from.isoformat(),
        "valid_until": plan.valid_until.isoformat(),
        "primary": _candidate_to_dict(plan.primary),
        "backups": [_candidate_to_dict(item) for item in plan.backups],
    }


def _plan_from_dict(value: dict[str, Any]) -> TradePlan:
    return TradePlan(
        plan_id=value["plan_id"],
        decision_at=datetime.fromisoformat(value["decision_at"]),
        valid_from=datetime.fromisoformat(value["valid_from"]),
        valid_until=datetime.fromisoformat(value["valid_until"]),
        primary=_candidate_from_dict(value["primary"]),
        backups=tuple(_candidate_from_dict(item) for item in value["backups"]),
    )


def state_to_dict(state: BrokerState) -> dict[str, Any]:
    open_plan = None
    if state.open_plan is not None:
        open_plan = {
            "plan": _plan_to_dict(state.open_plan.plan),
            "reserved_cash": str(state.open_plan.reserved_cash),
            "reserved_positions": [
                {"symbol": item.symbol, "quantity": item.quantity}
                for item in state.open_plan.reserved_positions
            ],
        }
    return {
        "schema_version": state.schema_version,
        "state_version": state.state_version,
        "initial_cash": str(state.initial_cash),
        "cash_total": str(state.cash_total),
        "cash_reserved": str(state.cash_reserved),
        "positions": [
            {
                "symbol": item.symbol,
                "quantity": item.quantity,
                "reserved_quantity": item.reserved_quantity,
                "average_cost": str(item.average_cost),
                "latest_price": (
                    str(item.latest_price) if item.latest_price is not None else None
                ),
                "latest_price_at": (
                    item.latest_price_at.isoformat()
                    if item.latest_price_at is not None
                    else None
                ),
            }
            for item in state.positions
        ],
        "open_plan": open_plan,
        "next_plan_number": state.next_plan_number,
        "next_order_number": state.next_order_number,
        "settled_through": (
            state.settled_through.isoformat()
            if state.settled_through is not None
            else None
        ),
        "daily_directions": [
            {
                "trading_date": item.trading_date.isoformat(),
                "symbol": item.symbol,
                "side": item.side.value,
            }
            for item in state.daily_directions
        ],
    }


def state_from_dict(value: dict[str, Any]) -> BrokerState:
    try:
        open_value = value["open_plan"]
        open_plan = None
        if open_value is not None:
            open_plan = StoredOpenPlan(
                plan=_plan_from_dict(open_value["plan"]),
                reserved_cash=Decimal(open_value["reserved_cash"]),
                reserved_positions=tuple(
                    PositionReservation(item["symbol"], item["quantity"])
                    for item in open_value["reserved_positions"]
                ),
            )
        return BrokerState(
            schema_version=value["schema_version"],
            state_version=value["state_version"],
            initial_cash=Decimal(value["initial_cash"]),
            cash_total=Decimal(value["cash_total"]),
            cash_reserved=Decimal(value["cash_reserved"]),
            positions=tuple(
                PositionState(
                    symbol=item["symbol"],
                    quantity=item["quantity"],
                    reserved_quantity=item["reserved_quantity"],
                    average_cost=Decimal(item["average_cost"]),
                    latest_price=(
                        Decimal(item["latest_price"])
                        if item["latest_price"] is not None
                        else None
                    ),
                    latest_price_at=(
                        datetime.fromisoformat(item["latest_price_at"])
                        if item["latest_price_at"] is not None
                        else None
                    ),
                )
                for item in value["positions"]
            ),
            open_plan=open_plan,
            next_plan_number=value["next_plan_number"],
            next_order_number=value["next_order_number"],
            settled_through=(
                datetime.fromisoformat(value["settled_through"])
                if value["settled_through"] is not None
                else None
            ),
            daily_directions=tuple(
                DailyDirection(
                    trading_date=date.fromisoformat(item["trading_date"]),
                    symbol=item["symbol"],
                    side=Side(item["side"]),
                )
                for item in value["daily_directions"]
            ),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise StateCorruptError("state.json has an invalid schema") from error


class StateStore:
    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.state_path = self.directory / "state.json"
        self.ledger = Ledger(self.directory / "ledger.jsonl")
        self._lock_path = self.directory / ".broker.lock"
        self._transaction_path = self.directory / ".broker-transaction.json"

    @contextmanager
    def _lock(self) -> Iterator[None]:
        self.directory.mkdir(parents=True, exist_ok=True)
        with self._lock_path.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _atomic_json(self, path: Path, value: dict[str, Any]) -> None:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=self.directory,
            prefix=f".{path.name}.",
            suffix=".tmp",
            text=True,
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(
                    value,
                    handle,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                )
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, path)
            directory_fd = os.open(self.directory, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)

    def _read_state_unlocked(self) -> BrokerState:
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise StateCorruptError("cannot read a valid state.json") from error
        if not isinstance(value, dict):
            raise StateCorruptError("state.json root must be an object")
        return state_from_dict(value)

    def _recover_unlocked(self) -> None:
        if not self._transaction_path.exists():
            return
        try:
            transaction = json.loads(
                self._transaction_path.read_text(encoding="utf-8")
            )
            events = transaction["events"]
            state_value = transaction["state"]
            if not isinstance(events, list) or not isinstance(state_value, dict):
                raise TypeError
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
            raise StateCorruptError("pending transaction is corrupt") from error
        self.ledger.append_missing(events)
        self._atomic_json(self.state_path, state_value)
        self._transaction_path.unlink()
        directory_fd = os.open(self.directory, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)

    def _commit_unlocked(
        self,
        state: BrokerState,
        events: Iterable[dict[str, Any]],
        *,
        transaction_id: str | None = None,
    ) -> None:
        transaction_id = transaction_id or uuid.uuid4().hex
        enriched_events = []
        for index, event in enumerate(events):
            if "event_id" in event or "transaction_id" in event:
                raise ValueError("caller events cannot provide transaction metadata")
            enriched_events.append(
                {
                    "event_id": f"{transaction_id}:{index}",
                    "transaction_id": transaction_id,
                    **event,
                }
            )
        transaction = {
            "transaction_id": transaction_id,
            "state": state_to_dict(state),
            "events": enriched_events,
        }
        self._atomic_json(self._transaction_path, transaction)
        self.ledger.append_missing(enriched_events)
        self._atomic_json(self.state_path, transaction["state"])
        self._transaction_path.unlink()
        directory_fd = os.open(self.directory, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)

    def initialize(
        self,
        initial_cash: Decimal,
        *,
        occurred_at: datetime,
    ) -> BrokerState:
        with self._lock():
            self._recover_unlocked()
            if self.state_path.exists():
                state = self._read_state_unlocked()
                if state.initial_cash != initial_cash:
                    raise InitialCashMismatchError(
                        "configured initial cash "
                        f"{initial_cash} does not match existing account "
                        f"{state.initial_cash}"
                    )
                return state
            state = initial_state(initial_cash)
            self._commit_unlocked(
                state,
                (
                    {
                        "event": "account_initialized",
                        "occurred_at": occurred_at.isoformat(),
                        "initial_cash": str(initial_cash),
                        "state_version": state.state_version,
                    },
                ),
            )
            return state

    def load(self) -> BrokerState:
        with self._lock():
            self._recover_unlocked()
            if not self.state_path.exists():
                raise FileNotFoundError(self.state_path)
            return self._read_state_unlocked()

    def commit(
        self,
        previous_version: int,
        state: BrokerState,
        events: Iterable[dict[str, Any]],
        *,
        transaction_id: str | None = None,
    ) -> BrokerState:
        with self._lock():
            self._recover_unlocked()
            current = self._read_state_unlocked()
            if current.state_version != previous_version:
                raise StateConflictError(
                    f"expected state version {previous_version}, "
                    f"found {current.state_version}"
                )
            if state.state_version == previous_version:
                state = replace(state, state_version=previous_version + 1)
            elif state.state_version != previous_version + 1:
                raise StateConflictError(
                    "new state version must be exactly one greater than current"
                )
            self._commit_unlocked(state, events, transaction_id=transaction_id)
            return state
