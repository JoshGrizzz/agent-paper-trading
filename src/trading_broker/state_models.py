"""Persistent broker-state models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from .models import Side, TradePlan
from .submission import AccountSnapshot, IntradayDirection, Position


_NEW_YORK = ZoneInfo("America/New_York")
SCHEMA_VERSION = 1


def _non_negative_decimal(value: Decimal, field_name: str) -> None:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be a Decimal")
    if not value.is_finite() or value < 0:
        raise ValueError(f"{field_name} must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class PositionState:
    symbol: str
    quantity: int
    reserved_quantity: int
    average_cost: Decimal
    latest_price: Decimal | None = None
    latest_price_at: datetime | None = None

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        if not symbol:
            raise ValueError("symbol must not be empty")
        for value, name in (
            (self.quantity, "quantity"),
            (self.reserved_quantity, "reserved_quantity"),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
            if value < 0:
                raise ValueError(f"{name} must not be negative")
        if self.quantity <= 0:
            raise ValueError("stored positions must have positive quantity")
        if self.reserved_quantity > self.quantity:
            raise ValueError("reserved_quantity cannot exceed quantity")
        _non_negative_decimal(self.average_cost, "average_cost")
        if self.latest_price is not None:
            _non_negative_decimal(self.latest_price, "latest_price")
            if self.latest_price == 0:
                raise ValueError("latest_price must be positive")
        if (self.latest_price is None) != (self.latest_price_at is None):
            raise ValueError("latest_price and latest_price_at must appear together")
        if self.latest_price_at is not None:
            if (
                self.latest_price_at.tzinfo is None
                or self.latest_price_at.utcoffset() is None
            ):
                raise ValueError("latest_price_at must be timezone-aware")
        object.__setattr__(self, "symbol", symbol)

    @property
    def available_quantity(self) -> int:
        return self.quantity - self.reserved_quantity


@dataclass(frozen=True, slots=True)
class PositionReservation:
    symbol: str
    quantity: int

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        if not symbol:
            raise ValueError("symbol must not be empty")
        if isinstance(self.quantity, bool) or not isinstance(self.quantity, int):
            raise TypeError("quantity must be an integer")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        object.__setattr__(self, "symbol", symbol)


@dataclass(frozen=True, slots=True)
class StoredOpenPlan:
    plan: TradePlan
    reserved_cash: Decimal
    reserved_positions: tuple[PositionReservation, ...] = ()

    def __post_init__(self) -> None:
        _non_negative_decimal(self.reserved_cash, "reserved_cash")
        reservations = tuple(self.reserved_positions)
        if len({item.symbol for item in reservations}) != len(reservations):
            raise ValueError("reserved_positions must contain unique symbols")
        object.__setattr__(self, "reserved_positions", reservations)


@dataclass(frozen=True, slots=True)
class DailyDirection:
    trading_date: date
    symbol: str
    side: Side

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        if not symbol:
            raise ValueError("symbol must not be empty")
        if not isinstance(self.side, Side):
            raise TypeError("side must be a Side")
        object.__setattr__(self, "symbol", symbol)


@dataclass(frozen=True, slots=True)
class BrokerState:
    schema_version: int
    state_version: int
    initial_cash: Decimal
    cash_total: Decimal
    cash_reserved: Decimal
    positions: tuple[PositionState, ...]
    open_plan: StoredOpenPlan | None
    next_plan_number: int
    next_order_number: int
    settled_through: datetime | None
    daily_directions: tuple[DailyDirection, ...] = ()

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version {self.schema_version}")
        for value, name in (
            (self.state_version, "state_version"),
            (self.next_plan_number, "next_plan_number"),
            (self.next_order_number, "next_order_number"),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        for value, name in (
            (self.initial_cash, "initial_cash"),
            (self.cash_total, "cash_total"),
            (self.cash_reserved, "cash_reserved"),
        ):
            _non_negative_decimal(value, name)
        if self.cash_reserved > self.cash_total:
            raise ValueError("cash_reserved cannot exceed cash_total")

        positions = tuple(self.positions)
        directions = tuple(self.daily_directions)
        if len({item.symbol for item in positions}) != len(positions):
            raise ValueError("positions must contain unique symbols")
        direction_keys = {(item.trading_date, item.symbol) for item in directions}
        if len(direction_keys) != len(directions):
            raise ValueError("daily_directions must be unique by date and symbol")
        if self.settled_through is not None and (
            self.settled_through.tzinfo is None
            or self.settled_through.utcoffset() is None
        ):
            raise ValueError("settled_through must be timezone-aware")

        expected_cash = self.open_plan.reserved_cash if self.open_plan else Decimal("0")
        if self.cash_reserved != expected_cash:
            raise ValueError("cash_reserved must equal the open plan reservation")
        expected_positions = (
            {item.symbol: item.quantity for item in self.open_plan.reserved_positions}
            if self.open_plan
            else {}
        )
        actual_positions = {
            item.symbol: item.reserved_quantity
            for item in positions
            if item.reserved_quantity
        }
        if actual_positions != expected_positions:
            raise ValueError("position reservations must equal the open plan reservation")

        object.__setattr__(self, "positions", positions)
        object.__setattr__(self, "daily_directions", directions)

    def account_snapshot(self, as_of: datetime) -> AccountSnapshot:
        local_date = as_of.astimezone(_NEW_YORK).date()
        return AccountSnapshot(
            as_of=as_of,
            cash_total=self.cash_total,
            cash_reserved=self.cash_reserved,
            positions=tuple(
                Position(item.symbol, item.quantity, item.reserved_quantity)
                for item in self.positions
            ),
            intraday_directions=tuple(
                IntradayDirection(item.symbol, item.side)
                for item in self.daily_directions
                if item.trading_date == local_date
            ),
        )


def initial_state(initial_cash: Decimal) -> BrokerState:
    _non_negative_decimal(initial_cash, "initial_cash")
    if initial_cash == 0:
        raise ValueError("initial_cash must be positive")
    return BrokerState(
        schema_version=SCHEMA_VERSION,
        state_version=1,
        initial_cash=initial_cash,
        cash_total=initial_cash,
        cash_reserved=Decimal("0"),
        positions=(),
        open_plan=None,
        next_plan_number=1,
        next_order_number=1,
        settled_through=None,
        daily_directions=(),
    )
