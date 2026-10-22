from datetime import datetime
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from trading_broker.cli import _is_public_error, _write_internal_diagnostic
from trading_broker.service import ServiceError


ET = ZoneInfo("America/New_York")
NOW = datetime(2026, 10, 20, 8, 0, tzinfo=ET)


class BrokerCliTests(unittest.TestCase):
    def test_expected_public_errors_do_not_require_private_diagnostics(self) -> None:
        self.assertTrue(_is_public_error(ValueError("bad input")))
        self.assertTrue(_is_public_error(ServiceError("TEST", "test", {})))
        self.assertFalse(_is_public_error(RuntimeError("boom")))

    def test_internal_diagnostic_is_private_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            try:
                raise RuntimeError("boom")
            except RuntimeError as error:
                with patch.dict(os.environ, {"BROKER_DATA_DIR": directory}):
                    _write_internal_diagnostic("status", error, NOW)

            path = Path(directory) / "internal_errors.jsonl"
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            document = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(document["command"], "status")
            self.assertEqual(document["error_type"], "RuntimeError")
            self.assertEqual(document["message"], "boom")
            self.assertIn("RuntimeError: boom", document["traceback"])


if __name__ == "__main__":
    unittest.main()
