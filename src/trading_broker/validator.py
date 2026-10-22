"""Pure submission validation against one immutable account snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from .models import (
    CandidateName,
    CandidatePlan,
    LimitOrder,
    Side,
    TradePlan,
)
from .submission import (
    AccountSnapshot,
    BrokerErrorCode,
    CandidateRequest,
    PlanRequest,
)


@dataclass(frozen=True, slots=True)
class SymbolQuantity:
    symbol: str
    quantity: int


@dataclass(frozen=True, slots=True)
class CandidateResources:
    candidate: CandidateName
    cash_required: Decimal
    sell_quantities: tuple[SymbolQuantity, ...]


@dataclass(frozen=True, slots=True)
class Reservation:
    cash: Decimal
    positions: tuple[SymbolQuantity, ...]


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: BrokerErrorCode
    message: str
    details: tuple[tuple[str, Any], ...] = ()


@dataclass(frozen=True, slots=True)
class CandidateRejection:
    candidate: CandidateName
    issue: ValidationIssue


@dataclass(frozen=True, slots=True)
class ValidationResult:
    plan: TradePlan
    resources: tuple[CandidateResources, ...]
    rejections: tuple[CandidateRejection, ...]
    reservation: Reservation
    next_order_number: int


class PlanValidationError(ValueError):
    def __init__(self, candidate: CandidateName, issue: ValidationIssue) -> None:
        self.candidate = candidate
        self.issue = issue
        super().__init__(f"{candidate.value}: {issue.code.value}: {issue.message}")


def _candidate_resources(
    candidate: CandidateName,
    request: CandidateRequest,
) -> CandidateResources:
    cash_required = sum(
        (
            order.quantity * order.limit_price
            for order in request.orders
            if order.side is Side.BUY
        ),
        start=Decimal("0"),
    )
    sells: dict[str, int] = {}
    for order in request.orders:
        if order.side is Side.SELL:
            sells[order.symbol] = sells.get(order.symbol, 0) + order.quantity
    return CandidateResources(
        candidate=candidate,
        cash_required=cash_required,
        sell_quantities=tuple(
            SymbolQuantity(symbol, quantity)
            for symbol, quantity in sorted(sells.items())
        ),
    )


def _find_issue(
    request: CandidateRequest,
    resources: CandidateResources,
    snapshot: AccountSnapshot,
    allowed_symbols: frozenset[str],
) -> ValidationIssue | None:
    for order in request.orders:
        if order.symbol not in allowed_symbols:
            return ValidationIssue(
                BrokerErrorCode.SYMBOL_NOT_ALLOWED,
                f"symbol {order.symbol} is not in the frozen universe",
                (("symbol", order.symbol),),
            )

    sides_by_symbol: dict[str, set[Side]] = {}
    for order in request.orders:
        sides_by_symbol.setdefault(order.symbol, set()).add(order.side)
    for symbol in sorted(sides_by_symbol):
        sides = sides_by_symbol[symbol]
        if len(sides) > 1:
            return ValidationIssue(
                BrokerErrorCode.CONFLICTING_ORDERS,
                f"candidate contains both buy and sell orders for {symbol}",
                (("symbol", symbol),),
            )

    for symbol in sorted(sides_by_symbol):
        requested_side = next(iter(sides_by_symbol[symbol]))
        existing_side = snapshot.intraday_side(symbol)
        if existing_side is not None and existing_side is not requested_side:
            return ValidationIssue(
                BrokerErrorCode.DAY_TRADE_RESTRICTED,
                f"{symbol} already has a {existing_side.value} fill today",
                (
                    ("symbol", symbol),
                    ("filled_side", existing_side.value),
                    ("requested_side", requested_side.value),
                ),
            )

    if resources.cash_required > snapshot.cash_available:
        return ValidationIssue(
            BrokerErrorCode.INSUFFICIENT_CASH,
            "required cash exceeds available cash",
            (
                ("required", str(resources.cash_required)),
                ("available", str(snapshot.cash_available)),
            ),
        )

    for item in resources.sell_quantities:
        available = snapshot.available_quantity(item.symbol)
        if item.quantity > available:
            return ValidationIssue(
                BrokerErrorCode.INSUFFICIENT_POSITION,
                f"sell quantity exceeds available position for {item.symbol}",
                (
                    ("symbol", item.symbol),
                    ("required", item.quantity),
                    ("available", available),
                ),
            )
    return None


def _accepted_candidate(
    name: CandidateName,
    request: CandidateRequest,
    first_order_number: int,
) -> tuple[CandidatePlan, int]:
    orders = tuple(
        LimitOrder(
            order_id=f"ord_{first_order_number + index:06d}",
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            limit_price=order.limit_price,
        )
        for index, order in enumerate(request.orders)
    )
    return CandidatePlan(name=name, orders=orders), first_order_number + len(orders)


def validate_plan_request(
    request: PlanRequest,
    snapshot: AccountSnapshot,
    allowed_symbols: frozenset[str],
    *,
    plan_id: str,
    decision_at: datetime,
    valid_from: datetime,
    valid_until: datetime,
    first_order_number: int = 1,
) -> ValidationResult:
    """Validate candidates independently and assign IDs only to accepted orders."""

    if isinstance(first_order_number, bool) or not isinstance(first_order_number, int):
        raise TypeError("first_order_number must be an integer")
    if first_order_number <= 0:
        raise ValueError("first_order_number must be positive")
    normalized_symbols = frozenset(symbol.strip().upper() for symbol in allowed_symbols)
    if not normalized_symbols:
        raise ValueError("allowed_symbols must not be empty")

    names = (CandidateName.PRIMARY, CandidateName.BACKUP_1, CandidateName.BACKUP_2)
    requests = (request.primary, *request.backups)
    accepted_candidates: list[CandidatePlan] = []
    accepted_resources: list[CandidateResources] = []
    rejections: list[CandidateRejection] = []
    next_order_number = first_order_number

    for index, candidate_request in enumerate(requests):
        name = names[index]
        resources = _candidate_resources(name, candidate_request)
        issue = _find_issue(
            candidate_request,
            resources,
            snapshot,
            normalized_symbols,
        )
        if issue is not None:
            if name is CandidateName.PRIMARY:
                raise PlanValidationError(name, issue)
            accepted_candidates.append(
                CandidatePlan(
                    name=name,
                    orders=(),
                    accepted=False,
                    rejection_reason=issue.message,
                )
            )
            rejections.append(CandidateRejection(name, issue))
            continue

        accepted, next_order_number = _accepted_candidate(
            name,
            candidate_request,
            next_order_number,
        )
        accepted_candidates.append(accepted)
        accepted_resources.append(resources)

    primary = accepted_candidates[0]
    backups = tuple(accepted_candidates[1:])
    cash_reserved = max(
        (item.cash_required for item in accepted_resources),
        default=Decimal("0"),
    )
    position_maxima: dict[str, int] = {}
    for resources in accepted_resources:
        for item in resources.sell_quantities:
            position_maxima[item.symbol] = max(
                position_maxima.get(item.symbol, 0),
                item.quantity,
            )

    return ValidationResult(
        plan=TradePlan(
            plan_id=plan_id,
            decision_at=decision_at,
            valid_from=valid_from,
            valid_until=valid_until,
            primary=primary,
            backups=backups,
        ),
        resources=tuple(accepted_resources),
        rejections=tuple(rejections),
        reservation=Reservation(
            cash=cash_reserved,
            positions=tuple(
                SymbolQuantity(symbol, quantity)
                for symbol, quantity in sorted(position_maxima.items())
            ),
        ),
        next_order_number=next_order_number,
    )
