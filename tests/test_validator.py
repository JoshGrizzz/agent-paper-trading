from datetime import datetime
from decimal import Decimal
import unittest
from zoneinfo import ZoneInfo

from trading_broker import (
    AccountSnapshot,
    BrokerErrorCode,
    CandidateName,
    CandidateRequest,
    IntradayDirection,
    OrderRequest,
    PlanRequest,
    PlanValidationError,
    Position,
    Side,
    validate_plan_request,
)


D = Decimal
ET = ZoneInfo("America/New_York")


def at(hour: int) -> datetime:
    return datetime(2026, 1, 5, hour, tzinfo=ET)


def requested(
    symbol: str,
    side: Side,
    quantity: int,
    limit_price: str,
) -> OrderRequest:
    return OrderRequest(symbol, side, quantity, D(limit_price))


def candidate(*orders: OrderRequest) -> CandidateRequest:
    return CandidateRequest(orders)


def account(
    *,
    cash_total: str = "1000",
    cash_reserved: str = "100",
    positions: tuple[Position, ...] = (),
    directions: tuple[IntradayDirection, ...] = (),
) -> AccountSnapshot:
    return AccountSnapshot(
        as_of=at(8),
        cash_total=D(cash_total),
        cash_reserved=D(cash_reserved),
        positions=positions,
        intraday_directions=directions,
    )


def validate(
    request: PlanRequest,
    snapshot: AccountSnapshot,
    *,
    first_order_number: int = 1,
):
    return validate_plan_request(
        request,
        snapshot,
        frozenset({"AAPL", "MSFT", "SPY", "QQQ", "NVDA"}),
        plan_id="plan_000001",
        decision_at=at(8),
        valid_from=at(8),
        valid_until=at(11),
        first_order_number=first_order_number,
    )


class ValidatorTests(unittest.TestCase):
    def test_candidates_use_same_snapshot_and_reserve_maximum_not_sum(self) -> None:
        request = PlanRequest(
            primary=candidate(requested("SPY", Side.BUY, 1, "500")),
            backups=(
                candidate(requested("QQQ", Side.BUY, 2, "400")),
                candidate(requested("AAPL", Side.SELL, 5, "200")),
            ),
        )
        result = validate(
            request,
            account(positions=(Position("AAPL", 10, 2),)),
            first_order_number=7,
        )
        self.assertEqual(result.reservation.cash, D("800"))
        self.assertEqual(
            [(item.symbol, item.quantity) for item in result.reservation.positions],
            [("AAPL", 5)],
        )
        order_ids = [
            order.order_id
            for item in (
                result.plan.primary,
                *result.plan.backups,
            )
            for order in item.orders
        ]
        self.assertEqual(order_ids, ["ord_000007", "ord_000008", "ord_000009"])
        self.assertEqual(result.next_order_number, 10)

    def test_position_reservation_is_maximum_across_candidates(self) -> None:
        request = PlanRequest(
            primary=candidate(requested("AAPL", Side.SELL, 5, "200")),
            backups=(candidate(requested("AAPL", Side.SELL, 7, "210")),),
        )
        result = validate(
            request,
            account(
                cash_reserved="0",
                positions=(Position("AAPL", 10),),
            ),
        )
        self.assertEqual(result.reservation.positions[0].quantity, 7)

    def test_invalid_backup_is_rejected_without_rejecting_backup_2(self) -> None:
        request = PlanRequest(
            primary=candidate(requested("SPY", Side.BUY, 1, "500")),
            backups=(
                candidate(requested("QQQ", Side.BUY, 3, "400")),
                candidate(requested("NVDA", Side.BUY, 2, "100")),
            ),
        )
        result = validate(request, account())
        self.assertTrue(result.plan.primary.accepted)
        self.assertFalse(result.plan.backups[0].accepted)
        self.assertEqual(result.plan.backups[0].orders, ())
        self.assertTrue(result.plan.backups[1].accepted)
        self.assertEqual(
            result.rejections[0].issue.code,
            BrokerErrorCode.INSUFFICIENT_CASH,
        )
        self.assertEqual(result.plan.primary.orders[0].order_id, "ord_000001")
        self.assertEqual(result.plan.backups[1].orders[0].order_id, "ord_000002")

    def test_invalid_primary_rejects_whole_submission(self) -> None:
        request = PlanRequest(
            primary=candidate(requested("SPY", Side.BUY, 2, "500")),
        )
        with self.assertRaises(PlanValidationError) as caught:
            validate(request, account())
        self.assertIs(caught.exception.candidate, CandidateName.PRIMARY)
        self.assertIs(
            caught.exception.issue.code,
            BrokerErrorCode.INSUFFICIENT_CASH,
        )

    def test_expected_sell_proceeds_cannot_fund_buys(self) -> None:
        request = PlanRequest(
            primary=candidate(
                requested("AAPL", Side.SELL, 5, "200"),
                requested("SPY", Side.BUY, 2, "500"),
            )
        )
        with self.assertRaises(PlanValidationError) as caught:
            validate(
                request,
                account(positions=(Position("AAPL", 5),)),
            )
        self.assertIs(
            caught.exception.issue.code,
            BrokerErrorCode.INSUFFICIENT_CASH,
        )

    def test_sell_cannot_exceed_available_position(self) -> None:
        request = PlanRequest(
            primary=candidate(requested("AAPL", Side.SELL, 9, "200")),
        )
        with self.assertRaises(PlanValidationError) as caught:
            validate(
                request,
                account(positions=(Position("AAPL", 10, 2),)),
            )
        self.assertIs(
            caught.exception.issue.code,
            BrokerErrorCode.INSUFFICIENT_POSITION,
        )

    def test_symbol_must_be_in_frozen_universe(self) -> None:
        request = PlanRequest(
            primary=candidate(requested("NOTREAL", Side.BUY, 1, "10")),
        )
        with self.assertRaises(PlanValidationError) as caught:
            validate(request, account())
        self.assertIs(
            caught.exception.issue.code,
            BrokerErrorCode.SYMBOL_NOT_ALLOWED,
        )

    def test_same_candidate_cannot_buy_and_sell_same_symbol(self) -> None:
        request = PlanRequest(
            primary=candidate(
                requested("AAPL", Side.BUY, 1, "190"),
                requested("AAPL", Side.SELL, 1, "210"),
            )
        )
        with self.assertRaises(PlanValidationError) as caught:
            validate(
                request,
                account(positions=(Position("AAPL", 5),)),
            )
        self.assertIs(
            caught.exception.issue.code,
            BrokerErrorCode.CONFLICTING_ORDERS,
        )

    def test_intraday_opposite_direction_is_rejected(self) -> None:
        request = PlanRequest(
            primary=candidate(requested("AAPL", Side.SELL, 1, "210")),
        )
        with self.assertRaises(PlanValidationError) as caught:
            validate(
                request,
                account(
                    positions=(Position("AAPL", 5),),
                    directions=(IntradayDirection("AAPL", Side.BUY),),
                ),
            )
        self.assertIs(
            caught.exception.issue.code,
            BrokerErrorCode.DAY_TRADE_RESTRICTED,
        )


if __name__ == "__main__":
    unittest.main()
