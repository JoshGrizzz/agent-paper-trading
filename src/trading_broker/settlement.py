"""Apply deterministic matcher results to persistent account state."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Any
from zoneinfo import ZoneInfo

from .market_cache import market_batch_checksum
from .market_data import MarketBatch
from .matcher import match_trade_plan
from .models import Fill, MatchStatus, PlanMatchResult, Side
from .state_models import BrokerState, DailyDirection, PositionState


_NEW_YORK = ZoneInfo("America/New_York")


class SettlementStatus(StrEnum):
    SELECTED = "selected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class SettlementOutcome:
    state: BrokerState
    status: SettlementStatus
    match: PlanMatchResult
    events: tuple[dict[str, Any], ...]


def accepted_plan_symbols(state: BrokerState) -> tuple[str, ...]:
    if state.open_plan is None:
        return ()
    return tuple(
        sorted(
            {
                order.symbol
                for candidate in (
                    state.open_plan.plan.primary,
                    *state.open_plan.plan.backups,
                )
                if candidate.accepted
                for order in candidate.orders
            }
        )
    )


def _fill_event(fill: Fill, batch: MarketBatch, plan_id: str) -> dict[str, Any]:
    bar = fill.bar
    return {
        "event": "order_filled",
        "occurred_at": bar.start_at.isoformat(),
        "plan_id": plan_id,
        "candidate": fill.candidate.value,
        "order_id": fill.order_id,
        "symbol": fill.symbol,
        "side": fill.side.value,
        "quantity": fill.quantity,
        "limit_price": str(fill.limit_price),
        "fill_price": str(fill.price),
        "notional": str(fill.notional),
        "trigger_bar": {
            "start_at": bar.start_at.isoformat(),
            "open": str(bar.open),
            "high": str(bar.high),
            "low": str(bar.low),
            "close": str(bar.close),
            "volume": bar.volume,
        },
        "market_data": {
            "provider": batch.provider,
            "provider_version": batch.provider_version,
            "fetched_at": batch.fetched_at.isoformat(),
            "interval": batch.request.interval,
            "prepost": batch.request.prepost,
            "auto_adjust": batch.request.auto_adjust,
            "actions": batch.request.actions,
            "keepna": batch.request.keepna,
            "sha256": market_batch_checksum(batch),
        },
    }


def _apply_fills(
    state: BrokerState,
    fills: tuple[Fill, ...],
) -> tuple[Decimal, tuple[PositionState, ...], tuple[DailyDirection, ...]]:
    cash = state.cash_total
    positions = {
        item.symbol: replace(item, reserved_quantity=0)
        for item in state.positions
    }
    directions = {
        (item.trading_date, item.symbol): item
        for item in state.daily_directions
    }

    for fill in fills:
        existing = positions.get(fill.symbol)
        if fill.side is Side.BUY:
            cash -= fill.notional
            if cash < 0:
                raise RuntimeError("validated buy fills produced negative cash")
            if existing is None:
                positions[fill.symbol] = PositionState(
                    symbol=fill.symbol,
                    quantity=fill.quantity,
                    reserved_quantity=0,
                    average_cost=fill.price,
                    latest_price=fill.price,
                    latest_price_at=fill.bar.start_at,
                )
            else:
                new_quantity = existing.quantity + fill.quantity
                new_cost = (
                    existing.average_cost * existing.quantity + fill.notional
                ) / new_quantity
                positions[fill.symbol] = replace(
                    existing,
                    quantity=new_quantity,
                    average_cost=new_cost,
                    latest_price=fill.price,
                    latest_price_at=fill.bar.start_at,
                )
        else:
            if existing is None or existing.quantity < fill.quantity:
                raise RuntimeError("validated sell fill exceeds stored position")
            cash += fill.notional
            new_quantity = existing.quantity - fill.quantity
            if new_quantity == 0:
                del positions[fill.symbol]
            else:
                positions[fill.symbol] = replace(
                    existing,
                    quantity=new_quantity,
                    latest_price=fill.price,
                    latest_price_at=fill.bar.start_at,
                )

        trading_date = fill.bar.start_at.astimezone(_NEW_YORK).date()
        key = (trading_date, fill.symbol)
        previous = directions.get(key)
        if previous is not None and previous.side is not fill.side:
            raise RuntimeError("settlement would violate the intraday direction rule")
        directions[key] = DailyDirection(trading_date, fill.symbol, fill.side)

    return (
        cash,
        tuple(sorted(positions.values(), key=lambda item: item.symbol)),
        tuple(
            sorted(
                directions.values(),
                key=lambda item: (item.trading_date, item.symbol),
            )
        ),
    )


def mark_positions(
    positions: tuple[PositionState, ...],
    batch: MarketBatch,
) -> tuple[PositionState, ...]:
    """Mark covered positions with the latest usable close in the batch."""

    position_symbols = {item.symbol for item in positions}
    latest_by_symbol = {}
    for bar in batch.bars:
        if bar.symbol not in position_symbols or not bar.is_usable:
            continue
        previous = latest_by_symbol.get(bar.symbol)
        if previous is None or bar.start_at > previous.start_at:
            latest_by_symbol[bar.symbol] = bar

    marked = []
    for position in positions:
        bar = latest_by_symbol.get(position.symbol)
        if bar is None:
            marked.append(position)
            continue
        if (
            position.latest_price_at is not None
            and bar.start_at < position.latest_price_at
        ):
            marked.append(position)
            continue
        assert bar.close is not None
        marked.append(
            replace(
                position,
                latest_price=bar.close,
                latest_price_at=bar.start_at,
            )
        )
    return tuple(marked)


def settle_open_plan(
    state: BrokerState,
    batch: MarketBatch,
    *,
    no_fill_status: SettlementStatus = SettlementStatus.EXPIRED,
) -> SettlementOutcome:
    if state.open_plan is None:
        raise ValueError("there is no open plan to settle")
    if no_fill_status not in (SettlementStatus.EXPIRED, SettlementStatus.CANCELLED):
        raise ValueError("no_fill_status must be expired or cancelled")

    plan = state.open_plan.plan
    expected_symbols = set(accepted_plan_symbols(state))
    if not expected_symbols.issubset(batch.request.symbols):
        raise ValueError("market batch does not cover all accepted plan symbols")
    if batch.request.start > plan.valid_from or batch.request.end < plan.valid_until:
        raise ValueError("market batch does not cover the full plan interval")

    match = match_trade_plan(plan, batch.bars)
    fills = match.fills
    cash, positions, directions = _apply_fills(state, fills)
    positions = mark_positions(positions, batch)
    settled_through = plan.valid_until - timedelta(minutes=1)
    if state.settled_through is not None:
        settled_through = max(state.settled_through, settled_through)

    new_state = replace(
        state,
        cash_total=cash,
        cash_reserved=Decimal("0"),
        positions=positions,
        open_plan=None,
        settled_through=settled_through,
        daily_directions=directions,
    )

    events: list[dict[str, Any]] = []
    events.extend(_fill_event(fill, batch, plan.plan_id) for fill in fills)
    if match.status is MatchStatus.SELECTED:
        status = SettlementStatus.SELECTED
        events.append(
            {
                "event": "plan_selected",
                "occurred_at": plan.valid_until.isoformat(),
                "plan_id": plan.plan_id,
                "candidate": match.selected_candidate.value,
                "fill_count": len(fills),
            }
        )
    else:
        status = no_fill_status
        events.append(
            {
                "event": (
                    "plan_cancelled"
                    if status is SettlementStatus.CANCELLED
                    else "plan_expired"
                ),
                "occurred_at": plan.valid_until.isoformat(),
                "plan_id": plan.plan_id,
            }
        )
    events.append(
        {
            "event": "resources_released",
            "occurred_at": plan.valid_until.isoformat(),
            "plan_id": plan.plan_id,
            "cash": str(state.open_plan.reserved_cash),
            "positions": {
                item.symbol: item.quantity
                for item in state.open_plan.reserved_positions
            },
        }
    )
    return SettlementOutcome(new_state, status, match, tuple(events))
