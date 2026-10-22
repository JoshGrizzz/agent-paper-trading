from datetime import datetime
from decimal import Decimal
import unittest
from zoneinfo import ZoneInfo

from trading_broker.market_data import MarketBatch, MarketRequest
from trading_broker.models import (
    Bar,
    CandidateName,
    CandidatePlan,
    LimitOrder,
    Side,
    TradePlan,
)
from trading_broker.settlement import SettlementStatus, settle_open_plan
from trading_broker.state_models import (
    BrokerState,
    PositionReservation,
    PositionState,
    SCHEMA_VERSION,
    StoredOpenPlan,
)


ET = ZoneInfo("America/New_York")
D = Decimal


def at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 1, 5, hour, minute, tzinfo=ET)


def order(order_id: str, symbol: str, side: Side, quantity: int, limit: str):
    return LimitOrder(order_id, symbol, side, quantity, D(limit))


def plan(primary_orders, backups=()):
    return TradePlan(
        "plan_000001",
        at(8),
        at(8, 1),
        at(11),
        CandidatePlan(CandidateName.PRIMARY, tuple(primary_orders)),
        tuple(backups),
    )


def batch(*bars: Bar) -> MarketBatch:
    symbols = tuple(sorted({item.symbol for item in bars}))
    return MarketBatch(
        request=MarketRequest(symbols, at(8, 1), at(11)),
        fetched_at=at(11),
        provider="fake",
        provider_version="1",
        bars=bars,
    )


def state(
    trade_plan: TradePlan,
    *,
    cash: str,
    reserved_cash: str,
    positions=(),
    reserved_positions=(),
) -> BrokerState:
    return BrokerState(
        schema_version=SCHEMA_VERSION,
        state_version=1,
        initial_cash=D("100000"),
        cash_total=D(cash),
        cash_reserved=D(reserved_cash),
        positions=tuple(positions),
        open_plan=StoredOpenPlan(
            trade_plan,
            D(reserved_cash),
            tuple(reserved_positions),
        ),
        next_plan_number=2,
        next_order_number=10,
        settled_through=None,
    )


def bar(symbol: str, open_: str, high: str, low: str, close: str) -> Bar:
    return Bar(symbol, at(9, 30), D(open_), D(high), D(low), D(close), 1000)


class SettlementTests(unittest.TestCase):
    def test_buy_fill_updates_cash_position_cost_and_releases_cash(self) -> None:
        trade_plan = plan([order("o1", "AAPL", Side.BUY, 10, "100")])
        outcome = settle_open_plan(
            state(trade_plan, cash="100000", reserved_cash="1000"),
            batch(bar("AAPL", "99", "101", "98", "100")),
        )
        self.assertIs(outcome.status, SettlementStatus.SELECTED)
        self.assertEqual(outcome.state.cash_total, D("99010"))
        self.assertEqual(outcome.state.cash_reserved, D("0"))
        self.assertIsNone(outcome.state.open_plan)
        position = outcome.state.positions[0]
        self.assertEqual(position.quantity, 10)
        self.assertEqual(position.average_cost, D("99"))
        self.assertEqual(outcome.state.daily_directions[0].side, Side.BUY)

    def test_additional_buy_uses_weighted_average_cost(self) -> None:
        trade_plan = plan([order("o1", "AAPL", Side.BUY, 10, "110")])
        outcome = settle_open_plan(
            state(
                trade_plan,
                cash="99000",
                reserved_cash="1100",
                positions=(
                    PositionState("AAPL", 10, 0, D("90"), D("95"), at(8)),
                ),
            ),
            batch(bar("AAPL", "110", "111", "109", "110")),
        )
        self.assertEqual(outcome.state.positions[0].quantity, 20)
        self.assertEqual(outcome.state.positions[0].average_cost, D("100"))

    def test_sell_fill_updates_cash_and_releases_reserved_shares(self) -> None:
        trade_plan = plan([order("o1", "AAPL", Side.SELL, 5, "100")])
        outcome = settle_open_plan(
            state(
                trade_plan,
                cash="90000",
                reserved_cash="0",
                positions=(
                    PositionState("AAPL", 10, 5, D("80"), D("95"), at(8)),
                ),
                reserved_positions=(PositionReservation("AAPL", 5),),
            ),
            batch(bar("AAPL", "101", "102", "99", "100")),
        )
        self.assertEqual(outcome.state.cash_total, D("90505"))
        self.assertEqual(outcome.state.positions[0].quantity, 5)
        self.assertEqual(outcome.state.positions[0].reserved_quantity, 0)
        self.assertEqual(outcome.state.positions[0].average_cost, D("80"))

    def test_settlement_marks_position_with_latest_usable_close(self) -> None:
        trade_plan = plan([order("o1", "AAPL", Side.BUY, 10, "100")])
        outcome = settle_open_plan(
            state(trade_plan, cash="100000", reserved_cash="1000"),
            batch(
                bar("AAPL", "99", "101", "98", "100"),
                Bar(
                    "AAPL",
                    at(10, 59),
                    D("104"),
                    D("106"),
                    D("103"),
                    D("105"),
                    2000,
                ),
            ),
        )
        position = outcome.state.positions[0]
        self.assertEqual(position.average_cost, D("99"))
        self.assertEqual(position.latest_price, D("105"))
        self.assertEqual(position.latest_price_at, at(10, 59))

    def test_no_fill_expires_and_releases_all_resources(self) -> None:
        trade_plan = plan([order("o1", "AAPL", Side.BUY, 10, "90")])
        outcome = settle_open_plan(
            state(trade_plan, cash="100000", reserved_cash="900"),
            batch(bar("AAPL", "100", "101", "99", "100")),
        )
        self.assertIs(outcome.status, SettlementStatus.EXPIRED)
        self.assertEqual(outcome.state.cash_total, D("100000"))
        self.assertEqual(outcome.state.cash_reserved, D("0"))
        self.assertEqual(outcome.state.positions, ())
        self.assertEqual(outcome.events[-2]["event"], "plan_expired")

    def test_full_bar_and_provider_metadata_are_audited(self) -> None:
        trade_plan = plan([order("o1", "AAPL", Side.BUY, 1, "100")])
        outcome = settle_open_plan(
            state(trade_plan, cash="100000", reserved_cash="100"),
            batch(bar("AAPL", "99", "101", "98", "100")),
        )
        fill_event = outcome.events[0]
        self.assertEqual(fill_event["trigger_bar"]["low"], "98")
        self.assertEqual(fill_event["market_data"]["provider"], "fake")
        self.assertEqual(fill_event["market_data"]["interval"], "1m")
        self.assertEqual(len(fill_event["market_data"]["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
