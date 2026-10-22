"""Batch market-data requests and the optional Yahoo Finance adapter."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from importlib import import_module
from typing import Any, Protocol

from .models import Bar


class MarketDataUnavailable(RuntimeError):
    pass


_PRICE_QUANTUM = Decimal("0.0001")


@dataclass(frozen=True, slots=True)
class MarketRequest:
    symbols: tuple[str, ...]
    start: datetime
    end: datetime
    interval: str = "1m"
    prepost: bool = True
    auto_adjust: bool = False
    actions: bool = True
    keepna: bool = True

    def __post_init__(self) -> None:
        symbols = tuple(sorted({item.strip().upper() for item in self.symbols}))
        if not symbols or any(not item for item in symbols):
            raise ValueError("symbols must not be empty")
        for value, name in ((self.start, "start"), (self.end, "end")):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{name} must be timezone-aware")
        if self.start >= self.end:
            raise ValueError("start must be earlier than end")
        if self.interval != "1m":
            raise ValueError("the frozen market-data interval is 1m")
        if (
            self.prepost is not True
            or self.auto_adjust is not False
            or self.actions is not True
            or self.keepna is not True
        ):
            raise ValueError("market-data parameters do not match the frozen policy")
        object.__setattr__(self, "symbols", symbols)


@dataclass(frozen=True, slots=True)
class MarketBatch:
    request: MarketRequest
    fetched_at: datetime
    provider: str
    provider_version: str
    bars: tuple[Bar, ...]

    def __post_init__(self) -> None:
        if self.fetched_at.tzinfo is None or self.fetched_at.utcoffset() is None:
            raise ValueError("fetched_at must be timezone-aware")
        if not self.provider.strip() or not self.provider_version.strip():
            raise ValueError("provider metadata must not be empty")
        bars = tuple(self.bars)
        allowed = set(self.request.symbols)
        if any(item.symbol not in allowed for item in bars):
            raise ValueError("batch contains a symbol outside its request")
        if any(
            not self.request.start <= item.start_at < self.request.end
            for item in bars
        ):
            raise ValueError("batch contains a bar outside its request interval")
        object.__setattr__(
            self,
            "bars",
            tuple(sorted(bars, key=lambda item: (item.start_at, item.symbol))),
        )


class MarketDataProvider(Protocol):
    def fetch(self, request: MarketRequest) -> MarketBatch:
        ...


def yahoo_symbol(symbol: str) -> str:
    return symbol.replace(".", "-")


def build_yahoo_download_arguments(request: MarketRequest) -> dict[str, Any]:
    return {
        "tickers": [yahoo_symbol(item) for item in request.symbols],
        "start": request.start,
        "end": request.end,
        "interval": request.interval,
        "prepost": request.prepost,
        "auto_adjust": request.auto_adjust,
        "actions": request.actions,
        "keepna": request.keepna,
        "group_by": "ticker",
        "threads": True,
        "ignore_tz": False,
        "progress": False,
        "multi_level_index": True,
        "timeout": 30,
    }


def _decimal_or_none(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        if bool(math.isnan(value)):  # type: ignore[arg-type]
            return None
    except (TypeError, ValueError):
        pass
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not result.is_finite():
        return None
    return result.quantize(_PRICE_QUANTUM, rounding=ROUND_HALF_EVEN)


def _volume_or_none(value: object) -> int | None:
    decimal = _decimal_or_none(value)
    if decimal is None or decimal < 0 or decimal != decimal.to_integral_value():
        return None
    return int(decimal)


class YahooFinanceProvider:
    """Lazy adapter so importing the broker does not require yfinance."""

    def __init__(self, yfinance_module: object | None = None) -> None:
        self._module = yfinance_module

    def _yfinance(self) -> object:
        if self._module is not None:
            return self._module
        try:
            self._module = import_module("yfinance")
        except ImportError as error:
            raise MarketDataUnavailable(
                "yfinance is not installed; install the market-data extra"
            ) from error
        return self._module

    def fetch(self, request: MarketRequest) -> MarketBatch:
        module = self._yfinance()
        try:
            data = module.download(**build_yahoo_download_arguments(request))
        except Exception as error:
            raise MarketDataUnavailable("Yahoo Finance batch download failed") from error
        if data is None:
            raise MarketDataUnavailable("Yahoo Finance returned no data object")

        bars: list[Bar] = []
        level_zero = set(data.columns.get_level_values(0))
        for original_symbol in request.symbols:
            provider_symbol = yahoo_symbol(original_symbol)
            try:
                if provider_symbol in level_zero:
                    frame = data[provider_symbol]
                elif original_symbol in level_zero:
                    frame = data[original_symbol]
                elif len(request.symbols) == 1:
                    frame = data.droplevel(1, axis=1)
                else:
                    raise KeyError(provider_symbol)
            except (KeyError, ValueError) as error:
                raise MarketDataUnavailable(
                    f"Yahoo Finance omitted requested symbol {original_symbol}"
                ) from error

            for timestamp, row in frame.iterrows():
                start_at = timestamp.to_pydatetime()
                if start_at.tzinfo is None or start_at.utcoffset() is None:
                    raise MarketDataUnavailable(
                        "Yahoo Finance returned timezone-naive intraday data"
                    )
                if not request.start <= start_at < request.end:
                    continue
                bars.append(
                    Bar(
                        symbol=original_symbol,
                        start_at=start_at,
                        open=_decimal_or_none(row.get("Open")),
                        high=_decimal_or_none(row.get("High")),
                        low=_decimal_or_none(row.get("Low")),
                        close=_decimal_or_none(row.get("Close")),
                        volume=_volume_or_none(row.get("Volume")),
                    )
                )

        version = str(getattr(module, "__version__", "unknown"))
        return MarketBatch(
            request=request,
            fetched_at=datetime.now(timezone.utc),
            provider="yahoo_finance",
            provider_version=version,
            bars=tuple(bars),
        )
