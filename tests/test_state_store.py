from dataclasses import replace
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
from zoneinfo import ZoneInfo

from trading_broker.state_models import initial_state
from trading_broker.state_store import (
    StateConflictError,
    StateStore,
    state_from_dict,
    state_to_dict,
)


ET = ZoneInfo("America/New_York")
D = Decimal


class StateStoreTests(unittest.TestCase):
    def test_initialization_creates_snapshot_and_ledger_event(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = StateStore(directory)
            state = store.initialize(
                D("100000"),
                occurred_at=datetime(2026, 1, 5, 8, tzinfo=ET),
            )
            self.assertEqual(state.cash_total, D("100000"))
            self.assertTrue((Path(directory) / "state.json").exists())
            events = store.ledger.read_all()
            self.assertEqual(events[0]["event"], "account_initialized")

    def test_state_round_trip_preserves_decimal_values(self) -> None:
        state = initial_state(D("100000.00"))
        restored = state_from_dict(state_to_dict(state))
        self.assertEqual(restored, state)
        self.assertIsInstance(restored.cash_total, Decimal)

    def test_commit_updates_snapshot_and_appends_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = StateStore(directory)
            old = store.initialize(
                D("100000"),
                occurred_at=datetime(2026, 1, 5, 8, tzinfo=ET),
            )
            proposed = replace(old, cash_total=D("99000"))
            committed = store.commit(
                old.state_version,
                proposed,
                (
                    {
                        "event": "test_adjustment",
                        "occurred_at": datetime(2026, 1, 5, 9, tzinfo=ET).isoformat(),
                        "amount": "-1000",
                    },
                ),
                transaction_id="test-transaction",
            )
            self.assertEqual(committed.state_version, 2)
            self.assertEqual(store.load().cash_total, D("99000"))
            events = store.ledger.read_all()
            self.assertEqual([event["event"] for event in events], [
                "account_initialized",
                "test_adjustment",
            ])

    def test_stale_writer_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = StateStore(directory)
            old = store.initialize(
                D("100000"),
                occurred_at=datetime(2026, 1, 5, 8, tzinfo=ET),
            )
            store.commit(old.state_version, replace(old, cash_total=D("99000")), ())
            with self.assertRaises(StateConflictError):
                store.commit(old.state_version, old, ())

    def test_pending_transaction_is_replayed_idempotently(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = StateStore(directory)
            old = store.initialize(
                D("100000"),
                occurred_at=datetime(2026, 1, 5, 8, tzinfo=ET),
            )
            target = replace(old, state_version=2, cash_total=D("98000"))
            event = {
                "event_id": "recovery:0",
                "transaction_id": "recovery",
                "event": "recovered_adjustment",
            }
            transaction = {
                "transaction_id": "recovery",
                "state": state_to_dict(target),
                "events": [event],
            }
            store._transaction_path.write_text(
                json.dumps(transaction) + "\n",
                encoding="utf-8",
            )
            store.ledger.append_missing([event])

            recovered = store.load()
            self.assertEqual(recovered.cash_total, D("98000"))
            matching = [
                item
                for item in store.ledger.read_all()
                if item["event_id"] == "recovery:0"
            ]
            self.assertEqual(len(matching), 1)
            self.assertFalse(store._transaction_path.exists())


if __name__ == "__main__":
    unittest.main()
