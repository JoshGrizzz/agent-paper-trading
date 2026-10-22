import unittest

from trading_broker import (
    BrokerErrorCode,
    PlanInputError,
    Side,
    parse_plan_json,
    parse_plan_payload,
)


class PlanIoTests(unittest.TestCase):
    def test_parses_buy_and_sell_into_typed_requests(self) -> None:
        request = parse_plan_json(
            """
            {
              "primary": {
                "orders": [
                  {
                    "symbol": "aapl",
                    "side": "buy",
                    "quantity": 2,
                    "limit_price": "190.25"
                  }
                ]
              },
              "backups": [
                {
                  "orders": [
                    {
                      "symbol": "AAPL",
                      "side": "sell",
                      "quantity": 1,
                      "limit_price": "210.00"
                    }
                  ]
                }
              ]
            }
            """
        )
        self.assertIs(request.primary.orders[0].side, Side.BUY)
        self.assertIs(request.backups[0].orders[0].side, Side.SELL)
        self.assertEqual(request.primary.orders[0].symbol, "AAPL")
        self.assertEqual(str(request.primary.orders[0].limit_price), "190.25")

    def test_rejects_market_order_or_any_unknown_field(self) -> None:
        payload = {
            "primary": {
                "orders": [
                    {
                        "symbol": "SPY",
                        "side": "buy",
                        "quantity": 1,
                        "limit_price": "500",
                        "order_type": "market",
                    }
                ]
            }
        }
        with self.assertRaises(PlanInputError) as caught:
            parse_plan_payload(payload)
        self.assertIn("unknown field", str(caught.exception))

    def test_rejects_broker_owned_fields(self) -> None:
        payload = {
            "primary": {
                "orders": [
                    {
                        "symbol": "SPY",
                        "side": "buy",
                        "quantity": 1,
                        "limit_price": "500",
                    }
                ]
            },
            "valid_until": "2026-01-05T11:00:00-05:00",
        }
        with self.assertRaises(PlanInputError):
            parse_plan_payload(payload)

    def test_price_must_be_a_decimal_string(self) -> None:
        payload = {
            "primary": {
                "orders": [
                    {
                        "symbol": "SPY",
                        "side": "buy",
                        "quantity": 1,
                        "limit_price": 500.0,
                    }
                ]
            }
        }
        with self.assertRaises(PlanInputError) as caught:
            parse_plan_payload(payload)
        self.assertIn("decimal string", str(caught.exception))

    def test_rejects_unknown_side_and_boolean_quantity(self) -> None:
        base_order = {
            "symbol": "SPY",
            "side": "short",
            "quantity": 1,
            "limit_price": "500",
        }
        with self.assertRaises(PlanInputError):
            parse_plan_payload({"primary": {"orders": [base_order]}})

        base_order["side"] = "buy"
        base_order["quantity"] = True
        with self.assertRaises(PlanInputError):
            parse_plan_payload({"primary": {"orders": [base_order]}})

    def test_rejects_empty_candidate(self) -> None:
        with self.assertRaises(PlanInputError):
            parse_plan_payload({"primary": {"orders": []}})

    def test_more_than_two_backups_has_specific_error_code(self) -> None:
        order = {
            "symbol": "SPY",
            "side": "buy",
            "quantity": 1,
            "limit_price": "500",
        }
        payload = {
            "primary": {"orders": [order]},
            "backups": [
                {"orders": [order]},
                {"orders": [order]},
                {"orders": [order]},
            ],
        }
        with self.assertRaises(PlanInputError) as caught:
            parse_plan_payload(payload)
        self.assertIs(caught.exception.code, BrokerErrorCode.TOO_MANY_BACKUPS)

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with self.assertRaises(PlanInputError):
            parse_plan_json(
                '{"primary":{"orders":[]},"primary":{"orders":[]}}'
            )


if __name__ == "__main__":
    unittest.main()
