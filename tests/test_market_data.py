from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
from zoneinfo import ZoneInfo

from trading_broker.market_cache import MarketCache, MarketCacheCorruptError
from trading_broker.market_data import (
    MarketBatch,
    MarketRequest,
    _decimal_or_none,
    build_yahoo_download_arguments,
    yahoo_symbol,
)
from trading_broker.models import Bar


ET = ZoneInfo("America/New_York")
D = Decimal


def at(hour: int) -> datetime:
    return datetime(2026, 1, 5, hour, tzinfo=ET)


class FakeProvider:
    def __init__(self) -> None:
        self.calls = 0
        self.requests = []

    def fetch(self, request: MarketRequest) -> MarketBatch:
        self.calls += 1
        self.requests.append(request)
        return MarketBatch(
            request=request,
            fetched_at=at(11),
            provider="fake",
            provider_version="1",
            bars=tuple(
                Bar(
                    symbol=symbol,
                    start_at=at(9),
                    open=D("100"),
                    high=D("101"),
                    low=D("99"),
                    close=D("100"),
                    volume=1000,
                )
                for symbol in request.symbols
            ),
        )


class MarketDataTests(unittest.TestCase):
    def test_request_normalizes_and_batches_symbols(self) -> None:
        request = MarketRequest(("msft", "AAPL", "AAPL"), at(8), at(11))
        self.assertEqual(request.symbols, ("AAPL", "MSFT"))
        arguments = build_yahoo_download_arguments(request)
        self.assertEqual(arguments["tickers"], ["AAPL", "MSFT"])
        self.assertEqual(arguments["interval"], "1m")
        self.assertIs(arguments["prepost"], True)
        self.assertIs(arguments["auto_adjust"], False)
        self.assertIs(arguments["actions"], True)
        self.assertIs(arguments["keepna"], True)

    def test_dot_symbols_are_mapped_for_yahoo(self) -> None:
        self.assertEqual(yahoo_symbol("BRK.B"), "BRK-B")

    def test_yahoo_float_prices_are_normalized_to_four_decimals(self) -> None:
        self.assertEqual(_decimal_or_none(773.239990234375), D("773.2400"))

    def test_cache_calls_provider_once_for_entire_batch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache = MarketCache(directory)
            provider = FakeProvider()
            request = MarketRequest(("AAPL", "MSFT"), at(8), at(11))

            first = cache.get_or_fetch(request, provider)
            second = cache.get_or_fetch(request, provider)

            self.assertEqual(provider.calls, 1)
            self.assertEqual(provider.requests[0].symbols, ("AAPL", "MSFT"))
            self.assertEqual(first, second)
            self.assertEqual({item.symbol for item in first.bars}, {"AAPL", "MSFT"})

    def test_cache_is_reusable_by_another_instance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request = MarketRequest(("AAPL",), at(8), at(11))
            first_provider = FakeProvider()
            MarketCache(directory).get_or_fetch(request, first_provider)

            second_provider = FakeProvider()
            MarketCache(directory).get_or_fetch(request, second_provider)
            self.assertEqual(first_provider.calls, 1)
            self.assertEqual(second_provider.calls, 0)

    def test_checksum_corruption_is_detected_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache = MarketCache(directory)
            provider = FakeProvider()
            request = MarketRequest(("AAPL",), at(8), at(11))
            cache.get_or_fetch(request, provider)
            cache_file = next(
                item for item in Path(directory).glob("*.json")
            )
            document = json.loads(cache_file.read_text(encoding="utf-8"))
            document["payload"]["bars"][0]["close"] = "999"
            cache_file.write_text(json.dumps(document), encoding="utf-8")

            with self.assertRaises(MarketCacheCorruptError):
                cache.get_or_fetch(request, provider)
            self.assertEqual(provider.calls, 1)


if __name__ == "__main__":
    unittest.main()
