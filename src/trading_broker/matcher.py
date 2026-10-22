"""Pure, deterministic limit-order matching against OHLCV bars."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, time
from zoneinfo import ZoneInfo

from .models import (
    Bar,
    CandidateMatch,
    CandidateName,
    CandidatePlan,
    Fill,
    LimitOrder,
    MatchStatus,
    PlanMatchResult,
    Side,
    TradePlan,
)


_NEW_YORK = ZoneInfo("America/New_York")
_SESSION_START = time(8, 0)
_SESSION_END = time(20, 0)


def _inside_supported_session(value: datetime) -> bool:
    local_time = value.astimezone(_NEW_YORK).time().replace(tzinfo=None)
    return _SESSION_START <= local_time < _SESSION_END


def _eligible_bars(
    symbol: str,
    bars: Iterable[Bar],
    valid_from: datetime,
    valid_until: datetime,
) -> list[Bar]:
    return sorted(
        (
            bar
            for bar in bars
            if bar.symbol == symbol
            and valid_from <= bar.start_at < valid_until
            and _inside_supported_session(bar.start_at)
            and bar.is_usable
        ),
        key=lambda bar: bar.start_at,
    )


def match_limit_order(
    order: LimitOrder,
    bars: Iterable[Bar],
    valid_from: datetime,
    valid_until: datetime,
    candidate: CandidateName,
) -> Fill | None:
    """Return the first whole-order fill in the half-open validity interval."""

    for bar in _eligible_bars(order.symbol, bars, valid_from, valid_until):
        assert bar.open is not None
        assert bar.high is not None
        assert bar.low is not None

        fill_price = None
        if order.side is Side.BUY:
            if bar.open <= order.limit_price:
                fill_price = bar.open
            elif bar.low <= order.limit_price:
                fill_price = order.limit_price
        else:
            if bar.open >= order.limit_price:
                fill_price = bar.open
            elif bar.high >= order.limit_price:
                fill_price = order.limit_price

        if fill_price is not None:
            return Fill(
                candidate=candidate,
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                limit_price=order.limit_price,
                price=fill_price,
                bar=bar,
            )
    return None


def match_candidate(
    candidate: CandidatePlan,
    bars: Iterable[Bar],
    valid_from: datetime,
    valid_until: datetime,
) -> CandidateMatch:
    """Match all orders independently; market volume is not allocated."""

    if not candidate.accepted:
        raise ValueError("a rejected candidate cannot be matched")
    available_bars = tuple(bars)
    fills = tuple(
        fill
        for order in candidate.orders
        if (
            fill := match_limit_order(
                order,
                available_bars,
                valid_from,
                valid_until,
                candidate.name,
            )
        )
        is not None
    )
    return CandidateMatch(
        candidate=candidate.name,
        fills=tuple(sorted(fills, key=lambda fill: (fill.bar.start_at, fill.order_id))),
    )


def match_trade_plan(plan: TradePlan, bars: Iterable[Bar]) -> PlanMatchResult:
    """Select the first candidate with any fill: primary, backup_1, backup_2."""

    available_bars = tuple(bars)
    evaluated: list[CandidateName] = []
    skipped: list[CandidateName] = []

    for candidate in (plan.primary, *plan.backups):
        if not candidate.accepted:
            skipped.append(candidate.name)
            continue
        result = match_candidate(candidate, available_bars, plan.valid_from, plan.valid_until)
        evaluated.append(candidate.name)
        if result.has_fill:
            return PlanMatchResult(
                plan_id=plan.plan_id,
                status=MatchStatus.SELECTED,
                selected_candidate=candidate.name,
                fills=result.fills,
                evaluated_candidates=tuple(evaluated),
                skipped_rejected_candidates=tuple(skipped),
            )

    return PlanMatchResult(
        plan_id=plan.plan_id,
        status=MatchStatus.EXPIRED,
        selected_candidate=None,
        fills=(),
        evaluated_candidates=tuple(evaluated),
        skipped_rejected_candidates=tuple(skipped),
    )
