from datetime import datetime, timedelta
from decimal import Decimal
import tempfile
import unittest
from zoneinfo import ZoneInfo

from trading_broker.market_cache import MarketCache
from trading_broker.market_data import MarketBatch, MarketRequest
from trading_broker.models import Bar
from trading_broker.plan_io import parse_plan_payload
from trading_broker.service import BrokerService, ServiceError, submission_window
from trading_broker.state_store import StateStore


ET = ZoneInfo("America/New_York")
D = Decimal


def at(hour: int, minute: int = 0, second: int = 0) -> datetime:
    return datetime(2026, 1, 5, hour, minute, second, tzinfo=ET)


class MutableClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value


class FakeProvider:
    def __init__(self, *, fill: bool = True) -> None:
        self.calls = 0
        self.fill = fill
        self.requests: list[MarketRequest] = []
        self.price: Decimal | None = None

    def fetch(self, request: MarketRequest) -> MarketBatch:
        self.calls += 1
        self.requests.append(request)
        start_at = request.end - timedelta(minutes=1)
        price = self.price or (D("99") if self.fill else D("110"))
        bars = tuple(
            Bar(
                symbol,
                start_at,
                price,
                price + 1,
                price - 1,
                price,
                1000,
            )
            for symbol in request.symbols
        )
        return MarketBatch(
            request,
            request.end,
            "fake",
            "1",
            bars,
        )


def request(limit: str = "100"):
    return parse_plan_payload(
        {
            "primary": {
                "orders": [
                    {
                        "symbol": "AAPL",
                        "side": "buy",
                        "quantity": 10,
                        "limit_price": limit,
                    }
                ]
            }
        }
    )


class ServiceTests(unittest.TestCase):
    def test_submission_window_starts_at_next_complete_minute(self) -> None:
        self.assertEqual(
            submission_window(at(8, 3, 21)),
            (at(8, 4), at(12)),
        )
        self.assertEqual(
            submission_window(at(14, 0)),
            (at(14, 1), at(15, 30)),
        )
        self.assertEqual(
            submission_window(at(15, 30)),
            (at(15, 31), at(19)),
        )
        self.assertEqual(
            submission_window(at(19, 0)),
            (at(19, 1), at(20)),
        )
        with self.assertRaises(ServiceError):
            submission_window(at(19, 59))
        self.assertEqual(
            submission_window(
                at(19, 59),
                overnight_smoke_until_next_noon=True,
            ),
            (at(20), at(12) + timedelta(days=1)),
        )

    def test_submit_reserves_resources_without_calling_yahoo(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = FakeProvider()
            clock = MutableClock(at(8, 3, 21))
            service = BrokerService(
                StateStore(directory),
                MarketCache(f"{directory}/cache"),
                provider,
                frozenset({"AAPL"}),
                clock=clock,
            )
            result = service.submit_plan(request())
            self.assertTrue(result["ok"])
            self.assertEqual(result["reservation"]["cash"], "1000")
            self.assertEqual(provider.calls, 0)
            state = service.state_store.load()
            self.assertEqual(state.cash_reserved, D("1000"))
            self.assertEqual(state.open_plan.plan.valid_from, at(8, 4))

    def test_status_before_boundary_does_not_settle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = FakeProvider()
            clock = MutableClock(at(8, 3))
            service = BrokerService(
                StateStore(directory),
                MarketCache(f"{directory}/cache"),
                provider,
                frozenset({"AAPL"}),
                clock=clock,
            )
            service.submit_plan(request())
            clock.value = at(10, 59)
            status = service.status()
            self.assertEqual(provider.calls, 0)
            self.assertEqual(len(status["open_plans"]), 1)

    def test_prewake_settle_batches_once_and_later_status_reuses_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = FakeProvider()
            clock = MutableClock(at(8, 3))
            service = BrokerService(
                StateStore(directory),
                MarketCache(f"{directory}/cache"),
                provider,
                frozenset({"AAPL"}),
                clock=clock,
            )
            service.submit_plan(request())
            clock.value = at(12, 1)
            settled = service.settle()
            self.assertTrue(settled["settled"])
            self.assertEqual(provider.calls, 1)
            self.assertEqual(settled["positions"][0]["quantity"], 10)
            self.assertEqual(settled["account"]["cash"]["total"], "99010.00")

            status = service.status()
            self.assertEqual(provider.calls, 1)
            self.assertEqual(status["open_plans"], [])

    def test_refresh_valuation_marks_all_positions_through_completed_minute(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = FakeProvider()
            clock = MutableClock(at(8, 3))
            service = BrokerService(
                StateStore(directory),
                MarketCache(f"{directory}/cache"),
                provider,
                frozenset({"AAPL"}),
                clock=clock,
            )
            service.submit_plan(request())
            clock.value = at(12, 1)
            service.settle()
            provider.price = D("105")
            clock.value = at(12, 3, 27)

            refreshed = service.refresh_valuation()

            self.assertTrue(refreshed["refreshed"])
            self.assertEqual(provider.calls, 2)
            self.assertEqual(provider.requests[-1].symbols, ("AAPL",))
            self.assertEqual(provider.requests[-1].start, at(8))
            self.assertEqual(provider.requests[-1].end, at(12, 3))
            self.assertEqual(refreshed["positions"][0]["latest_price"], "105")
            self.assertEqual(
                refreshed["positions"][0]["latest_price_at"],
                at(12, 2).isoformat(),
            )
            self.assertEqual(refreshed["account"]["valuation_status"], "fresh")
            ledger = service.state_store.ledger.path.read_text(encoding="utf-8")
            self.assertIn('\"event\":\"valuation_refreshed\"', ledger)

    def test_refresh_valuation_without_positions_does_not_call_provider(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = FakeProvider()
            service = BrokerService(
                StateStore(directory),
                MarketCache(f"{directory}/cache"),
                provider,
                frozenset({"AAPL"}),
                clock=lambda: at(8, 30),
            )
            refreshed = service.refresh_valuation()
            self.assertFalse(refreshed["refreshed"])
            self.assertEqual(provider.calls, 0)

    def test_cancel_replays_complete_minutes_before_cancelling(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = FakeProvider(fill=False)
            clock = MutableClock(at(8, 3))
            service = BrokerService(
                StateStore(directory),
                MarketCache(f"{directory}/cache"),
                provider,
                frozenset({"AAPL"}),
                clock=clock,
            )
            submitted = service.submit_plan(request())
            plan_id = submitted["plan"]["plan_id"]
            clock.value = at(9, 0, 3)
            cancelled = service.cancel(plan_id)
            self.assertEqual(cancelled["plan"]["status"], "cancelled")
            self.assertEqual(provider.calls, 1)
            self.assertEqual(service.state_store.load().cash_reserved, D("0"))

    def test_cancel_fails_if_plan_filled_before_cutoff(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = FakeProvider(fill=True)
            clock = MutableClock(at(8, 3))
            service = BrokerService(
                StateStore(directory),
                MarketCache(f"{directory}/cache"),
                provider,
                frozenset({"AAPL"}),
                clock=clock,
            )
            plan_id = service.submit_plan(request())["plan"]["plan_id"]
            clock.value = at(9, 0, 3)
            with self.assertRaises(ServiceError) as caught:
                service.cancel(plan_id)
            self.assertEqual(caught.exception.code, "PLAN_NOT_OPEN")
            self.assertEqual(len(caught.exception.fills), 1)
            self.assertIsNone(service.state_store.load().open_plan)


if __name__ == "__main__":
    unittest.main()
