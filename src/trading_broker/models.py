"""Typed domain models for plans, market bars, and matching results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _require_positive_decimal(value: Decimal, field_name: str) -> None:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be a Decimal")
    if not value.is_finite() or value <= 0:
        raise ValueError(f"{field_name} must be finite and positive")


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


class CandidateName(StrEnum):
    PRIMARY = "primary"
    BACKUP_1 = "backup_1"
    BACKUP_2 = "backup_2"


class MatchStatus(StrEnum):
    SELECTED = "selected"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class LimitOrder:
    order_id: str
    symbol: str
    side: Side
    quantity: int
    limit_price: Decimal

    def __post_init__(self) -> None:
        order_id = self.order_id.strip()
        symbol = self.symbol.strip().upper()
        if not order_id:
            raise ValueError("order_id must not be empty")
        if not symbol:
            raise ValueError("symbol must not be empty")
        if not isinstance(self.side, Side):
            raise TypeError("side must be a Side")
        if isinstance(self.quantity, bool) or not isinstance(self.quantity, int):
            raise TypeError("quantity must be an integer")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        _require_positive_decimal(self.limit_price, "limit_price")
        object.__setattr__(self, "order_id", order_id)
        object.__setattr__(self, "symbol", symbol)


@dataclass(frozen=True, slots=True)
class CandidatePlan:
    name: CandidateName
    orders: tuple[LimitOrder, ...]
    accepted: bool = True
    rejection_reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, CandidateName):
            raise TypeError("name must be a CandidateName")
        orders = tuple(self.orders)
        object.__setattr__(self, "orders", orders)
        if self.accepted:
            if not orders:
                raise ValueError("an accepted candidate must contain at least one order")
            if self.rejection_reason is not None:
                raise ValueError("an accepted candidate cannot have a rejection_reason")
        else:
            if not self.rejection_reason or not self.rejection_reason.strip():
                raise ValueError("a rejected candidate must have a rejection_reason")


@dataclass(frozen=True, slots=True)
class TradePlan:
    plan_id: str
    decision_at: datetime
    valid_from: datetime
    valid_until: datetime
    primary: CandidatePlan
    backups: tuple[CandidatePlan, ...] = ()

    def __post_init__(self) -> None:
        plan_id = self.plan_id.strip()
        if not plan_id:
            raise ValueError("plan_id must not be empty")
        _require_aware(self.decision_at, "decision_at")
        _require_aware(self.valid_from, "valid_from")
        _require_aware(self.valid_until, "valid_until")
        if self.valid_from >= self.valid_until:
            raise ValueError("valid_from must be earlier than valid_until")
        if self.primary.name is not CandidateName.PRIMARY:
            raise ValueError("primary candidate must be named primary")
        if not self.primary.accepted:
            raise ValueError("a rejected primary plan cannot be submitted")

        backups = tuple(self.backups)
        object.__setattr__(self, "backups", backups)
        if len(backups) > 2:
            raise ValueError("at most two backup candidates are allowed")
        expected_names = (CandidateName.BACKUP_1, CandidateName.BACKUP_2)
        for index, backup in enumerate(backups):
            if backup.name is not expected_names[index]:
                raise ValueError("backup candidates must be ordered as backup_1, backup_2")

        order_ids = [
            order.order_id
            for candidate in (self.primary, *backups)
            for order in candidate.orders
        ]
        if len(order_ids) != len(set(order_ids)):
            raise ValueError("order_id values must be unique within a plan")
        object.__setattr__(self, "plan_id", plan_id)


@dataclass(frozen=True, slots=True)
class Bar:
    """A market bar as received from a data adapter.

    Price and volume fields are nullable so malformed provider rows can reach the
    deterministic validation boundary and be ignored instead of crashing a run.
    """

    symbol: str
    start_at: datetime
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal | None
    volume: int | None

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        if not symbol:
            raise ValueError("symbol must not be empty")
        _require_aware(self.start_at, "start_at")
        object.__setattr__(self, "symbol", symbol)

    @property
    def is_usable(self) -> bool:
        if isinstance(self.volume, bool) or not isinstance(self.volume, int):
            return False
        if self.volume <= 0:
            return False
        prices = (self.open, self.high, self.low, self.close)
        if any(not isinstance(price, Decimal) for price in prices):
            return False
        if any(not price.is_finite() or price <= 0 for price in prices if price is not None):
            return False
        assert self.open is not None
        assert self.high is not None
        assert self.low is not None
        assert self.close is not None
        return self.low <= self.open <= self.high and self.low <= self.close <= self.high


@dataclass(frozen=True, slots=True)
class Fill:
    candidate: CandidateName
    order_id: str
    symbol: str
    side: Side
    quantity: int
    limit_price: Decimal
    price: Decimal
    bar: Bar

    @property
    def notional(self) -> Decimal:
        return self.price * self.quantity


@dataclass(frozen=True, slots=True)
class CandidateMatch:
    candidate: CandidateName
    fills: tuple[Fill, ...]

    @property
    def has_fill(self) -> bool:
        return bool(self.fills)


@dataclass(frozen=True, slots=True)
class PlanMatchResult:
    plan_id: str
    status: MatchStatus
    selected_candidate: CandidateName | None
    fills: tuple[Fill, ...]
    evaluated_candidates: tuple[CandidateName, ...]
    skipped_rejected_candidates: tuple[CandidateName, ...]

    def __post_init__(self) -> None:
        if self.status is MatchStatus.SELECTED:
            if self.selected_candidate is None or not self.fills:
                raise ValueError("a selected result requires a candidate and at least one fill")
        elif self.selected_candidate is not None or self.fills:
            raise ValueError("an expired result cannot contain a selected candidate or fills")
