"""Strict parsing for agent-authored PLAN.json files."""

from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from .models import Side
from .submission import (
    BrokerErrorCode,
    CandidateRequest,
    OrderRequest,
    PlanRequest,
)


class PlanInputError(ValueError):
    def __init__(
        self,
        message: str,
        *,
        path: str = "$",
        code: BrokerErrorCode = BrokerErrorCode.INVALID_ARGUMENT,
    ) -> None:
        self.code = code
        self.path = path
        super().__init__(f"{path}: {message}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PlanInputError(f"duplicate field {key!r}")
        result[key] = value
    return result


def _require_object(value: object, path: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise PlanInputError("must be an object", path=path)
    return value


def _check_fields(
    value: Mapping[str, object],
    *,
    allowed: set[str],
    required: set[str],
    path: str,
) -> None:
    unknown = sorted(set(value) - allowed)
    missing = sorted(required - set(value))
    if unknown:
        raise PlanInputError(f"unknown field(s): {', '.join(unknown)}", path=path)
    if missing:
        raise PlanInputError(f"missing field(s): {', '.join(missing)}", path=path)


def _parse_order(value: object, path: str) -> OrderRequest:
    raw = _require_object(value, path)
    _check_fields(
        raw,
        allowed={"symbol", "side", "quantity", "limit_price"},
        required={"symbol", "side", "quantity", "limit_price"},
        path=path,
    )

    symbol = raw["symbol"]
    side_value = raw["side"]
    quantity = raw["quantity"]
    price_value = raw["limit_price"]
    if not isinstance(symbol, str):
        raise PlanInputError("symbol must be a string", path=f"{path}.symbol")
    if not isinstance(side_value, str):
        raise PlanInputError("side must be a string", path=f"{path}.side")
    try:
        side = Side(side_value)
    except ValueError as error:
        raise PlanInputError(
            "side must be exactly 'buy' or 'sell'",
            path=f"{path}.side",
        ) from error
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise PlanInputError("quantity must be an integer", path=f"{path}.quantity")
    if not isinstance(price_value, str):
        raise PlanInputError(
            "limit_price must be a decimal string",
            path=f"{path}.limit_price",
        )
    try:
        limit_price = Decimal(price_value)
    except InvalidOperation as error:
        raise PlanInputError(
            "limit_price must be a valid decimal string",
            path=f"{path}.limit_price",
        ) from error

    try:
        return OrderRequest(symbol, side, quantity, limit_price)
    except (TypeError, ValueError) as error:
        raise PlanInputError(str(error), path=path) from error


def _parse_candidate(value: object, path: str) -> CandidateRequest:
    raw = _require_object(value, path)
    _check_fields(raw, allowed={"orders"}, required={"orders"}, path=path)
    orders_value = raw["orders"]
    if not isinstance(orders_value, list):
        raise PlanInputError("orders must be an array", path=f"{path}.orders")
    try:
        orders = tuple(
            _parse_order(order, f"{path}.orders[{index}]")
            for index, order in enumerate(orders_value)
        )
        return CandidateRequest(orders)
    except PlanInputError:
        raise
    except (TypeError, ValueError) as error:
        raise PlanInputError(str(error), path=path) from error


def parse_plan_payload(payload: object) -> PlanRequest:
    raw = _require_object(payload, "$")
    _check_fields(raw, allowed={"primary", "backups"}, required={"primary"}, path="$")
    backups_value = raw.get("backups", [])
    if not isinstance(backups_value, list):
        raise PlanInputError("backups must be an array", path="$.backups")
    if len(backups_value) > 2:
        raise PlanInputError(
            "at most two backup candidates are allowed",
            path="$.backups",
            code=BrokerErrorCode.TOO_MANY_BACKUPS,
        )
    return PlanRequest(
        primary=_parse_candidate(raw["primary"], "$.primary"),
        backups=tuple(
            _parse_candidate(value, f"$.backups[{index}]")
            for index, value in enumerate(backups_value)
        ),
    )


def parse_plan_json(text: str) -> PlanRequest:
    try:
        payload = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as error:
        raise PlanInputError(
            f"invalid JSON at line {error.lineno}, column {error.colno}"
        ) from error
    return parse_plan_payload(payload)


def load_plan_file(path: str | Path) -> PlanRequest:
    return parse_plan_json(Path(path).read_text(encoding="utf-8"))


def load_symbol_universe(path: str | Path) -> frozenset[str]:
    symbols = {
        line.strip().upper()
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    if not symbols:
        raise ValueError("symbol universe must not be empty")
    return frozenset(symbols)
