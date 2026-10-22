"""Immutable models for an agent submission and its account snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from .models import Side


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


class BrokerErrorCode(StrEnum):
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    SYMBOL_NOT_ALLOWED = "SYMBOL_NOT_ALLOWED"
    INSUFFICIENT_CASH = "INSUFFICIENT_CASH"
    INSUFFICIENT_POSITION = "INSUFFICIENT_POSITION"
    DAY_TRADE_RESTRICTED = "DAY_TRADE_RESTRICTED"
    CONFLICTING_ORDERS = "CONFLICTING_ORDERS"
    TOO_MANY_BACKUPS = "TOO_MANY_BACKUPS"


@dataclass(frozen=True, slots=True)
class OrderRequest:
    """An order supplied by an agent before the broker assigns an ID."""

    symbol: str
    side: Side
    quantity: int
    limit_price: Decimal

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        if not symbol:
            raise ValueError("symbol must not be empty")
        if not isinstance(self.side, Side):
            raise TypeError("side must be a Side")
        if isinstance(self.quantity, bool) or not isinstance(self.quantity, int):
            raise TypeError("quantity must be an integer")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if not isinstance(self.limit_price, Decimal):
            raise TypeError("limit_price must be a Decimal")
        if not self.limit_price.is_finite() or self.limit_price <= 0:
            raise ValueError("limit_price must be finite and positive")
        object.__setattr__(self, "symbol", symbol)


@dataclass(frozen=True, slots=True)
class CandidateRequest:
    orders: tuple[OrderRequest, ...]

    def __post_init__(self) -> None:
        orders = tuple(self.orders)
        if not orders:
            raise ValueError("candidate orders must not be empty")
        object.__setattr__(self, "orders", orders)


@dataclass(frozen=True, slots=True)
class PlanRequest:
    primary: CandidateRequest
    backups: tuple[CandidateRequest, ...] = ()

    def __post_init__(self) -> None:
        backups = tuple(self.backups)
        if len(backups) > 2:
            raise ValueError("at most two backup candidates are allowed")
        object.__setattr__(self, "backups", backups)


@dataclass(frozen=True, slots=True)
class Position:
    symbol: str
    quantity: int
    reserved_quantity: int = 0

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
        if self.reserved_quantity > self.quantity:
            raise ValueError("reserved_quantity cannot exceed quantity")
        object.__setattr__(self, "symbol", symbol)

    @property
    def available_quantity(self) -> int:
        return self.quantity - self.reserved_quantity


@dataclass(frozen=True, slots=True)
class IntradayDirection:
    """Direction already filled for a symbol on the current trading day."""

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
class AccountSnapshot:
    as_of: datetime
    cash_total: Decimal
    cash_reserved: Decimal
    positions: tuple[Position, ...] = ()
    intraday_directions: tuple[IntradayDirection, ...] = ()

    def __post_init__(self) -> None:
        _require_aware(self.as_of, "as_of")
        for value, name in (
            (self.cash_total, "cash_total"),
            (self.cash_reserved, "cash_reserved"),
        ):
            if not isinstance(value, Decimal):
                raise TypeError(f"{name} must be a Decimal")
            if not value.is_finite() or value < 0:
                raise ValueError(f"{name} must be finite and non-negative")
        if self.cash_reserved > self.cash_total:
            raise ValueError("cash_reserved cannot exceed cash_total")

        positions = tuple(self.positions)
        directions = tuple(self.intraday_directions)
        if len({item.symbol for item in positions}) != len(positions):
            raise ValueError("positions must contain unique symbols")
        if len({item.symbol for item in directions}) != len(directions):
            raise ValueError("intraday_directions must contain unique symbols")
        object.__setattr__(self, "positions", positions)
        object.__setattr__(self, "intraday_directions", directions)

    @property
    def cash_available(self) -> Decimal:
        return self.cash_total - self.cash_reserved

    def available_quantity(self, symbol: str) -> int:
        normalized = symbol.strip().upper()
        return next(
            (item.available_quantity for item in self.positions if item.symbol == normalized),
            0,
        )

    def intraday_side(self, symbol: str) -> Side | None:
        normalized = symbol.strip().upper()
        return next(
            (item.side for item in self.intraday_directions if item.symbol == normalized),
            None,
        )
