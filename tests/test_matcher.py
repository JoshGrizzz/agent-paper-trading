from datetime import datetime
from decimal import Decimal
import unittest
from zoneinfo import ZoneInfo

from trading_broker import (
    Bar,
    CandidateName,
    CandidatePlan,
    LimitOrder,
    MatchStatus,
    Side,
    TradePlan,
    match_limit_order,
    match_trade_plan,
)


D = Decimal
ET = ZoneInfo("America/New_York")


def at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 1, 5, hour, minute, tzinfo=ET)


def make_bar(
    symbol: str,
    hour: int,
    minute: int,
    open_: str,
    high: str,
    low: str,
    close: str,
    volume: int | None = 1_000,
) -> Bar:
    return Bar(symbol, at(hour, minute), D(open_), D(high), D(low), D(close), volume)


def order(order_id: str, symbol: str, side: Side, limit: str) -> LimitOrder:
    return LimitOrder(order_id, symbol, side, 10, D(limit))


def candidate(name: CandidateName, *orders: LimitOrder) -> CandidatePlan:
    return CandidatePlan(name, orders)


def plan(
    primary: CandidatePlan,
    *backups: CandidatePlan,
    valid_from: datetime | None = None,
    valid_until: datetime | None = None,
) -> TradePlan:
    return TradePlan(
        plan_id="plan-1",
        decision_at=at(7, 55),
        valid_from=valid_from or at(8),
        valid_until=valid_until or at(11),
        primary=primary,
        backups=backups,
    )


class LimitOrderMatchingTests(unittest.TestCase):
    def test_buy_gap_through_gets_open_price_improvement(self) -> None:
        item = order("o1", "aapl", Side.BUY, "100")
        fill = match_limit_order(
            item,
            [make_bar("AAPL", 9, 30, "99", "101", "98", "100")],
            at(8),
            at(11),
            CandidateName.PRIMARY,
        )
        self.assertIsNotNone(fill)
        self.assertEqual(fill.price, D("99"))

    def test_buy_intrabar_touch_fills_at_limit(self) -> None:
        item = order("o1", "AAPL", Side.BUY, "100")
        fill = match_limit_order(
            item,
            [make_bar("AAPL", 9, 30, "101", "102", "99", "100.5")],
            at(8),
            at(11),
            CandidateName.PRIMARY,
        )
        self.assertEqual(fill.price, D("100"))

    def test_sell_gap_and_intrabar_rules(self) -> None:
        item = order("o1", "AAPL", Side.SELL, "100")
        gap_fill = match_limit_order(
            item,
            [make_bar("AAPL", 9, 30, "101", "102", "99", "100")],
            at(8),
            at(11),
            CandidateName.PRIMARY,
        )
        touch_fill = match_limit_order(
            item,
            [make_bar("AAPL", 9, 30, "99", "101", "98", "100")],
            at(8),
            at(11),
            CandidateName.PRIMARY,
        )
        self.assertEqual(gap_fill.price, D("101"))
        self.assertEqual(touch_fill.price, D("100"))

    def test_uses_earliest_qualifying_bar_even_when_input_is_unsorted(self) -> None:
        item = order("o1", "AAPL", Side.BUY, "100")
        fill = match_limit_order(
            item,
            [
                make_bar("AAPL", 10, 0, "98", "100", "97", "99"),
                make_bar("AAPL", 9, 40, "101", "102", "99", "100"),
            ],
            at(8),
            at(11),
            CandidateName.PRIMARY,
        )
        self.assertEqual(fill.bar.start_at, at(9, 40))
        self.assertEqual(fill.price, D("100"))

    def test_ignores_bad_rows_and_zero_volume(self) -> None:
        item = order("o1", "AAPL", Side.BUY, "100")
        bad_ohlc = make_bar("AAPL", 9, 30, "101", "100", "99", "101")
        zero_volume = make_bar("AAPL", 9, 40, "99", "101", "98", "100", 0)
        good = make_bar("AAPL", 9, 50, "99", "101", "98", "100")
        fill = match_limit_order(
            item,
            [bad_ohlc, zero_volume, good],
            at(8),
            at(11),
            CandidateName.PRIMARY,
        )
        self.assertEqual(fill.bar.start_at, at(9, 50))

    def test_enforces_supported_session_and_half_open_plan_window(self) -> None:
        item = order("o1", "AAPL", Side.BUY, "100")
        fill = match_limit_order(
            item,
            [
                make_bar("AAPL", 7, 50, "90", "91", "89", "90"),
                make_bar("AAPL", 8, 0, "99", "101", "98", "100"),
                make_bar("AAPL", 11, 0, "95", "96", "94", "95"),
            ],
            at(8),
            at(11),
            CandidateName.PRIMARY,
        )
        self.assertEqual(fill.bar.start_at, at(8))

        no_fill = match_limit_order(
            item,
            [make_bar("AAPL", 20, 0, "90", "91", "89", "90")],
            at(17),
            at(21),
            CandidateName.PRIMARY,
        )
        self.assertIsNone(no_fill)


class CandidateSelectionTests(unittest.TestCase):
    def test_any_primary_fill_selects_primary_without_mixing_backup(self) -> None:
        primary = candidate(
            CandidateName.PRIMARY,
            order("p-aapl", "AAPL", Side.BUY, "100"),
            order("p-msft", "MSFT", Side.BUY, "100"),
        )
        backup = candidate(
            CandidateName.BACKUP_1,
            order("b-nvda", "NVDA", Side.BUY, "200"),
        )
        result = match_trade_plan(
            plan(primary, backup),
            [
                make_bar("AAPL", 9, 30, "99", "101", "98", "100"),
                make_bar("MSFT", 9, 30, "110", "112", "109", "111"),
                make_bar("NVDA", 9, 30, "199", "201", "198", "200"),
            ],
        )
        self.assertEqual(result.status, MatchStatus.SELECTED)
        self.assertEqual(result.selected_candidate, CandidateName.PRIMARY)
        self.assertEqual([fill.order_id for fill in result.fills], ["p-aapl"])
        self.assertEqual(result.evaluated_candidates, (CandidateName.PRIMARY,))

    def test_all_fillable_orders_in_selected_candidate_are_returned(self) -> None:
        primary = candidate(
            CandidateName.PRIMARY,
            order("p-late", "MSFT", Side.BUY, "100"),
            order("p-early", "AAPL", Side.BUY, "100"),
        )
        result = match_trade_plan(
            plan(primary),
            [
                make_bar("MSFT", 10, 0, "99", "101", "98", "100"),
                make_bar("AAPL", 9, 30, "99", "101", "98", "100"),
            ],
        )
        self.assertEqual([fill.order_id for fill in result.fills], ["p-early", "p-late"])

    def test_falls_back_when_primary_has_no_fill(self) -> None:
        primary = candidate(
            CandidateName.PRIMARY,
            order("p1", "AAPL", Side.BUY, "90"),
        )
        backup = candidate(
            CandidateName.BACKUP_1,
            order("b1", "MSFT", Side.BUY, "100"),
        )
        result = match_trade_plan(
            plan(primary, backup),
            [
                make_bar("AAPL", 9, 30, "101", "102", "99", "100"),
                make_bar("MSFT", 9, 30, "99", "101", "98", "100"),
            ],
        )
        self.assertEqual(result.selected_candidate, CandidateName.BACKUP_1)
        self.assertEqual(
            result.evaluated_candidates,
            (CandidateName.PRIMARY, CandidateName.BACKUP_1),
        )

    def test_rejected_backup_is_skipped_without_blocking_backup_2(self) -> None:
        primary = candidate(
            CandidateName.PRIMARY,
            order("p1", "AAPL", Side.BUY, "90"),
        )
        rejected = CandidatePlan(
            CandidateName.BACKUP_1,
            (),
            accepted=False,
            rejection_reason="insufficient cash",
        )
        backup_2 = candidate(
            CandidateName.BACKUP_2,
            order("b2", "NVDA", Side.BUY, "200"),
        )
        result = match_trade_plan(
            plan(primary, rejected, backup_2),
            [make_bar("NVDA", 9, 30, "199", "201", "198", "200")],
        )
        self.assertEqual(result.selected_candidate, CandidateName.BACKUP_2)
        self.assertEqual(result.skipped_rejected_candidates, (CandidateName.BACKUP_1,))

    def test_expires_when_no_candidate_has_a_fill(self) -> None:
        primary = candidate(
            CandidateName.PRIMARY,
            order("p1", "AAPL", Side.BUY, "90"),
        )
        backup = candidate(
            CandidateName.BACKUP_1,
            order("b1", "MSFT", Side.BUY, "90"),
        )
        result = match_trade_plan(
            plan(primary, backup),
            [make_bar("AAPL", 9, 30, "100", "101", "99", "100")],
        )
        self.assertEqual(result.status, MatchStatus.EXPIRED)
        self.assertIsNone(result.selected_candidate)
        self.assertEqual(result.fills, ())


if __name__ == "__main__":
    unittest.main()
