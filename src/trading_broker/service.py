"""Application service joining state, validation, market data, and settlement."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from .market_cache import MarketCache, market_batch_checksum
from .market_data import (
    MarketDataProvider,
    MarketDataUnavailable,
    MarketRequest,
)
from .models import CandidatePlan, Fill, TradePlan
from .plan_io import load_symbol_universe
from .settlement import (
    SettlementOutcome,
    SettlementStatus,
    accepted_plan_symbols,
    mark_positions,
    settle_open_plan,
)
from .state_models import (
    BrokerState,
    PositionReservation,
    PositionState,
    StoredOpenPlan,
)
from .state_store import StateStore
from .submission import PlanRequest
from .validator import PlanValidationError, ValidationResult, validate_plan_request


_NEW_YORK = ZoneInfo("America/New_York")
_INITIAL_CASH = Decimal("100000.00")


@dataclass(frozen=True, slots=True)
class ServiceError(RuntimeError):
    code: str
    message: str
    details: dict[str, Any]
    fills: tuple[Fill, ...] = ()

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def submission_window(as_of: datetime) -> tuple[datetime, datetime]:
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")
    local = as_of.astimezone(_NEW_YORK)
    if local.weekday() >= 5:
        raise ServiceError(
            "INVALID_ARGUMENT",
            "new plans cannot be submitted on a weekend",
            {},
        )
    next_minute = local.replace(second=0, microsecond=0) + timedelta(minutes=1)
    session_start = datetime.combine(local.date(), time(8), _NEW_YORK)
    valid_from = max(next_minute, session_start)
    endpoints = (
        datetime.combine(local.date(), time(12), _NEW_YORK),
        datetime.combine(local.date(), time(15, 30), _NEW_YORK),
        datetime.combine(local.date(), time(19), _NEW_YORK),
        datetime.combine(local.date(), time(20), _NEW_YORK),
    )
    valid_until = next((item for item in endpoints if item > valid_from), None)
    if valid_until is None:
        raise ServiceError(
            "INVALID_ARGUMENT",
            "new plans must be submitted before 20:00 America/New_York",
            {},
        )
    return valid_from, valid_until


def _order_view(order: Any) -> dict[str, Any]:
    return {
        "order_id": order.order_id,
        "symbol": order.symbol,
        "side": order.side.value,
        "quantity": order.quantity,
        "limit_price": str(order.limit_price),
    }


def _candidate_view(candidate: CandidatePlan, priority: int | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "accepted" if candidate.accepted else "rejected",
        "orders": [_order_view(order) for order in candidate.orders],
    }
    if priority is not None:
        result["priority"] = priority
    if not candidate.accepted:
        result["error"] = {
            "code": "CANDIDATE_REJECTED",
            "message": candidate.rejection_reason,
        }
    return result


def plan_view(plan: TradePlan) -> dict[str, Any]:
    return {
        "plan_id": plan.plan_id,
        "submitted_at": plan.decision_at.isoformat(),
        "valid_from": plan.valid_from.isoformat(),
        "valid_until": plan.valid_until.isoformat(),
        "status": "pending",
        "primary": _candidate_view(plan.primary),
        "backups": [
            _candidate_view(candidate, index)
            for index, candidate in enumerate(plan.backups, start=1)
        ],
    }


def fill_view(fill: Fill) -> dict[str, Any]:
    return {
        "order_id": fill.order_id,
        "candidate": fill.candidate.value,
        "symbol": fill.symbol,
        "side": fill.side.value,
        "quantity": fill.quantity,
        "limit_price": str(fill.limit_price),
        "fill_price": str(fill.price),
        "filled_at": fill.bar.start_at.isoformat(),
    }


class BrokerService:
    def __init__(
        self,
        state_store: StateStore,
        market_cache: MarketCache,
        market_provider: MarketDataProvider,
        allowed_symbols: frozenset[str],
        *,
        clock: Callable[[], datetime],
        initial_cash: Decimal = _INITIAL_CASH,
    ) -> None:
        self.state_store = state_store
        self.market_cache = market_cache
        self.market_provider = market_provider
        self.allowed_symbols = allowed_symbols
        self.clock = clock
        self.initial_cash = initial_cash

    @classmethod
    def from_paths(
        cls,
        data_directory: str | Path,
        cache_directory: str | Path,
        universe_path: str | Path,
        market_provider: MarketDataProvider,
        *,
        clock: Callable[[], datetime],
    ) -> "BrokerService":
        return cls(
            StateStore(data_directory),
            MarketCache(cache_directory),
            market_provider,
            load_symbol_universe(universe_path),
            clock=clock,
        )

    def _now(self, value: datetime | None = None) -> datetime:
        result = value or self.clock()
        if result.tzinfo is None or result.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        return result.astimezone(_NEW_YORK)

    def _load(self, as_of: datetime) -> BrokerState:
        return self.state_store.initialize(
            self.initial_cash,
            occurred_at=as_of,
        )

    def _market_batch(self, state: BrokerState, end: datetime | None = None):
        if state.open_plan is None:
            raise ValueError("there is no open plan")
        plan = state.open_plan.plan
        request = MarketRequest(
            symbols=accepted_plan_symbols(state),
            start=plan.valid_from,
            end=end or plan.valid_until,
        )
        try:
            return self.market_cache.get_or_fetch(request, self.market_provider)
        except MarketDataUnavailable as error:
            raise ServiceError(
                "MARKET_DATA_UNAVAILABLE",
                str(error),
                {
                    "symbols": list(request.symbols),
                    "start": request.start.isoformat(),
                    "end": request.end.isoformat(),
                },
            ) from error

    def _settle_due(
        self,
        state: BrokerState,
        as_of: datetime,
    ) -> tuple[BrokerState, SettlementOutcome | None]:
        if state.open_plan is None or as_of < state.open_plan.plan.valid_until:
            return state, None
        batch = self._market_batch(state)
        outcome = settle_open_plan(state, batch)
        committed = self.state_store.commit(
            state.state_version,
            outcome.state,
            outcome.events,
        )
        return committed, replace(outcome, state=committed)

    def settle(self, *, as_of: datetime | None = None) -> dict[str, Any]:
        now = self._now(as_of)
        state = self._load(now)
        state, outcome = self._settle_due(state, now)
        result = self._status_document(state, now, outcome)
        result["command"] = "settle"
        result["settled"] = outcome is not None
        return result

    def refresh_valuation(self, *, as_of: datetime | None = None) -> dict[str, Any]:
        """Refresh every held symbol through the latest completed minute."""

        now = self._now(as_of)
        state = self._load(now)
        state, outcome = self._settle_due(state, now)
        symbols = tuple(sorted(item.symbol for item in state.positions))
        end = now.replace(second=0, microsecond=0)
        start = datetime.combine(now.date(), time(8), _NEW_YORK)

        if not symbols or end <= start:
            result = self._status_document(state, now, outcome)
            result["command"] = "refresh-valuation"
            result["refreshed"] = False
            result["valuation_refresh"] = {
                "symbols": list(symbols),
                "updated_symbols": [],
                "missing_symbols": list(symbols),
                "start": None,
                "end": None,
            }
            return result

        request = MarketRequest(symbols=symbols, start=start, end=end)
        try:
            batch = self.market_cache.get_or_fetch(request, self.market_provider)
        except MarketDataUnavailable as error:
            raise ServiceError(
                "MARKET_DATA_UNAVAILABLE",
                str(error),
                {
                    "symbols": list(request.symbols),
                    "start": request.start.isoformat(),
                    "end": request.end.isoformat(),
                },
            ) from error

        marked = mark_positions(state.positions, batch)
        before = {
            item.symbol: (item.latest_price, item.latest_price_at)
            for item in state.positions
        }
        updated_symbols = tuple(
            item.symbol
            for item in marked
            if (item.latest_price, item.latest_price_at) != before[item.symbol]
        )
        covered_symbols = {bar.symbol for bar in batch.bars if bar.is_usable}
        missing_symbols = tuple(
            symbol for symbol in symbols if symbol not in covered_symbols
        )
        proposed = replace(state, positions=marked)
        event = {
            "event": "valuation_refreshed",
            "occurred_at": now.isoformat(),
            "symbols": list(symbols),
            "updated_symbols": list(updated_symbols),
            "missing_symbols": list(missing_symbols),
            "market_data": {
                "provider": batch.provider,
                "provider_version": batch.provider_version,
                "fetched_at": batch.fetched_at.isoformat(),
                "start": request.start.isoformat(),
                "end": request.end.isoformat(),
                "interval": request.interval,
                "prepost": request.prepost,
                "sha256": market_batch_checksum(batch),
            },
        }
        committed = self.state_store.commit(
            state.state_version,
            proposed,
            (event,),
        )
        result = self._status_document(committed, now, outcome)
        result["command"] = "refresh-valuation"
        result["refreshed"] = True
        result["valuation_refresh"] = {
            "symbols": list(symbols),
            "updated_symbols": list(updated_symbols),
            "missing_symbols": list(missing_symbols),
            "start": request.start.isoformat(),
            "end": request.end.isoformat(),
        }
        return result

    def status(self, *, as_of: datetime | None = None) -> dict[str, Any]:
        now = self._now(as_of)
        state = self._load(now)
        state, outcome = self._settle_due(state, now)
        return self._status_document(state, now, outcome)

    def submit_plan(
        self,
        request: PlanRequest,
        *,
        as_of: datetime | None = None,
    ) -> dict[str, Any]:
        now = self._now(as_of)
        state = self._load(now)
        state, prior_outcome = self._settle_due(state, now)
        if state.open_plan is not None:
            raise ServiceError(
                "ACTIVE_PLAN_EXISTS",
                "an unsettled trading plan already exists",
                {"plan_id": state.open_plan.plan.plan_id},
                prior_outcome.match.fills if prior_outcome else (),
            )

        valid_from, valid_until = submission_window(now)
        plan_id = f"plan_{state.next_plan_number:06d}"
        try:
            validation = validate_plan_request(
                request,
                state.account_snapshot(now),
                self.allowed_symbols,
                plan_id=plan_id,
                decision_at=now,
                valid_from=valid_from,
                valid_until=valid_until,
                first_order_number=state.next_order_number,
            )
        except PlanValidationError as error:
            raise ServiceError(
                error.issue.code.value,
                error.issue.message,
                dict(error.issue.details),
                prior_outcome.match.fills if prior_outcome else (),
            ) from error

        proposed = self._reserve_for_plan(state, validation)
        events: list[dict[str, Any]] = [
            {
                "event": "plan_submitted",
                "occurred_at": now.isoformat(),
                "plan_id": plan_id,
                "valid_from": valid_from.isoformat(),
                "valid_until": valid_until.isoformat(),
                "reserved_cash": str(validation.reservation.cash),
                "reserved_positions": {
                    item.symbol: item.quantity
                    for item in validation.reservation.positions
                },
            }
        ]
        for rejection in validation.rejections:
            events.append(
                {
                    "event": "candidate_rejected",
                    "occurred_at": now.isoformat(),
                    "plan_id": plan_id,
                    "candidate": rejection.candidate.value,
                    "code": rejection.issue.code.value,
                    "message": rejection.issue.message,
                    "details": dict(rejection.issue.details),
                }
            )
        committed = self.state_store.commit(
            state.state_version,
            proposed,
            events,
        )
        return {
            "ok": True,
            "command": "submit-plan",
            "as_of": now.isoformat(),
            "settled_through": (
                committed.settled_through.isoformat()
                if committed.settled_through is not None
                else None
            ),
            "plan": plan_view(validation.plan),
            "reservation": {
                "cash": str(validation.reservation.cash),
                "positions": {
                    item.symbol: item.quantity
                    for item in validation.reservation.positions
                },
            },
            "fills": [
                fill_view(fill)
                for fill in (prior_outcome.match.fills if prior_outcome else ())
            ],
        }

    def _reserve_for_plan(
        self,
        state: BrokerState,
        validation: ValidationResult,
    ) -> BrokerState:
        reservation_by_symbol = {
            item.symbol: item.quantity
            for item in validation.reservation.positions
        }
        positions = tuple(
            replace(
                item,
                reserved_quantity=reservation_by_symbol.get(item.symbol, 0),
            )
            for item in state.positions
        )
        return replace(
            state,
            cash_reserved=validation.reservation.cash,
            positions=positions,
            open_plan=StoredOpenPlan(
                validation.plan,
                validation.reservation.cash,
                tuple(
                    PositionReservation(item.symbol, item.quantity)
                    for item in validation.reservation.positions
                ),
            ),
            next_plan_number=state.next_plan_number + 1,
            next_order_number=validation.next_order_number,
        )

    def cancel(
        self,
        plan_id: str,
        *,
        as_of: datetime | None = None,
    ) -> dict[str, Any]:
        now = self._now(as_of)
        state = self._load(now)
        state, due_outcome = self._settle_due(state, now)
        if state.open_plan is None:
            raise ServiceError(
                "PLAN_NOT_OPEN" if due_outcome else "PLAN_NOT_FOUND",
                "the plan is no longer open" if due_outcome else "plan not found",
                {"plan_id": plan_id},
                due_outcome.match.fills if due_outcome else (),
            )
        if state.open_plan.plan.plan_id != plan_id:
            raise ServiceError(
                "PLAN_NOT_FOUND",
                "plan not found",
                {"plan_id": plan_id},
            )

        original = state.open_plan
        cutoff = now.replace(second=0, microsecond=0)
        if cutoff <= original.plan.valid_from:
            proposed = self._release_without_replay(state)
            events = (
                {
                    "event": "plan_cancelled",
                    "occurred_at": now.isoformat(),
                    "plan_id": plan_id,
                },
                {
                    "event": "resources_released",
                    "occurred_at": now.isoformat(),
                    "plan_id": plan_id,
                    "cash": str(original.reserved_cash),
                    "positions": {
                        item.symbol: item.quantity
                        for item in original.reserved_positions
                    },
                },
            )
            committed = self.state_store.commit(
                state.state_version,
                proposed,
                events,
            )
            fills: tuple[Fill, ...] = ()
        else:
            shortened_plan = replace(original.plan, valid_until=cutoff)
            shortened_state = replace(
                state,
                open_plan=replace(original, plan=shortened_plan),
            )
            batch = self._market_batch(shortened_state, end=cutoff)
            outcome = settle_open_plan(
                shortened_state,
                batch,
                no_fill_status=SettlementStatus.CANCELLED,
            )
            committed = self.state_store.commit(
                state.state_version,
                outcome.state,
                outcome.events,
            )
            fills = outcome.match.fills
            if outcome.status is SettlementStatus.SELECTED:
                raise ServiceError(
                    "PLAN_NOT_OPEN",
                    "the plan produced fills before cancellation",
                    {"plan_id": plan_id},
                    fills,
                )

        return {
            "ok": True,
            "command": "cancel",
            "as_of": now.isoformat(),
            "settled_through": (
                committed.settled_through.isoformat()
                if committed.settled_through is not None
                else None
            ),
            "plan": {
                "plan_id": plan_id,
                "status": "cancelled",
                "cancelled_at": now.isoformat(),
            },
            "released": {
                "cash": str(original.reserved_cash),
                "positions": {
                    item.symbol: item.quantity
                    for item in original.reserved_positions
                },
            },
            "fills": [fill_view(fill) for fill in fills],
        }

    def _release_without_replay(self, state: BrokerState) -> BrokerState:
        return replace(
            state,
            cash_reserved=Decimal("0"),
            positions=tuple(
                replace(item, reserved_quantity=0)
                for item in state.positions
            ),
            open_plan=None,
        )

    def _status_document(
        self,
        state: BrokerState,
        as_of: datetime,
        outcome: SettlementOutcome | None,
    ) -> dict[str, Any]:
        position_views: list[dict[str, Any]] = []
        market_values: list[Decimal] = []
        valuation_status = "fresh"
        valuation_errors: list[dict[str, str]] = []
        for item in state.positions:
            price_status = None
            market_value = None
            unrealized = None
            if item.latest_price is None or item.latest_price_at is None:
                valuation_status = "incomplete"
                valuation_errors.append(
                    {"symbol": item.symbol, "reason": "no cached price"}
                )
            else:
                age = as_of - item.latest_price_at.astimezone(_NEW_YORK)
                price_status = (
                    "fresh"
                    if timedelta(0) <= age <= timedelta(minutes=5)
                    else "stale"
                )
                if price_status == "stale" and valuation_status == "fresh":
                    valuation_status = "stale"
                market_value = item.latest_price * item.quantity
                unrealized = (
                    item.latest_price - item.average_cost
                ) * item.quantity
                market_values.append(market_value)
            position_views.append(
                {
                    "symbol": item.symbol,
                    "quantity": item.quantity,
                    "reserved_quantity": item.reserved_quantity,
                    "available_quantity": item.available_quantity,
                    "average_cost": str(item.average_cost),
                    "latest_price": (
                        str(item.latest_price)
                        if item.latest_price is not None
                        else None
                    ),
                    "latest_price_at": (
                        item.latest_price_at.isoformat()
                        if item.latest_price_at is not None
                        else None
                    ),
                    "price_source": (
                        "yahoo_finance"
                        if item.latest_price is not None
                        else None
                    ),
                    "price_status": price_status,
                    "market_value": (
                        str(market_value) if market_value is not None else None
                    ),
                    "unrealized_pnl": (
                        str(unrealized) if unrealized is not None else None
                    ),
                }
            )

        complete = len(market_values) == len(state.positions)
        positions_value = sum(market_values, start=Decimal("0")) if complete else None
        equity = (
            state.cash_total + positions_value
            if positions_value is not None
            else None
        )
        fills = outcome.match.fills if outcome else ()
        return {
            "ok": True,
            "command": "status",
            "as_of": as_of.isoformat(),
            "settled_through": (
                state.settled_through.isoformat()
                if state.settled_through is not None
                else None
            ),
            "account": {
                "initial_cash": str(state.initial_cash),
                "cash": {
                    "total": str(state.cash_total),
                    "reserved": str(state.cash_reserved),
                    "available": str(state.cash_total - state.cash_reserved),
                },
                "positions_market_value": (
                    str(positions_value) if positions_value is not None else None
                ),
                "equity": str(equity) if equity is not None else None,
                "valuation_status": valuation_status,
                "valuation_errors": valuation_errors,
            },
            "positions": position_views,
            "open_plans": (
                [plan_view(state.open_plan.plan)]
                if state.open_plan is not None
                else []
            ),
            "fills": [fill_view(fill) for fill in fills],
        }
