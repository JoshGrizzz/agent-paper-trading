from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
from zoneinfo import ZoneInfo

from trading_broker.state_store import StateStore
from trading_runner.claude_successors import rollout_pairs
from trading_runner.claude_v2_smoke import prepare
from trading_runner.rollout_profile import load_profile, profile_document


NOW = datetime(2026, 10, 27, 23, 0, tzinfo=ZoneInfo("America/New_York"))


class ClaudeV2SmokeTests(unittest.TestCase):
    def project(self, root: Path) -> tuple[Path, Path]:
        (root / "templates").mkdir()
        rollouts = root / "rollouts"
        rollouts.mkdir()
        (root / "BROKER.md").write_text(
            "# Rules\n\n- 初始现金为 100,000 美元，所有金额以美元计。\n",
            encoding="utf-8",
        )
        (root / "universe.txt").write_text("SPY\n", encoding="utf-8")
        (root / "templates" / "DECISION_FORMAT.md").write_text(
            "format", encoding="utf-8"
        )
        (root / "templates" / "DECISIONS.md").write_text(
            "# decisions\n", encoding="utf-8"
        )
        (root / "broker").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
        (root / "broker").chmod(0o755)
        return root, rollouts

    def sources(self, rollouts: Path) -> dict[str, Decimal]:
        values: dict[str, Decimal] = {}
        for index, (source_id, _, _) in enumerate(
            rollout_pairs("official_claude_v2", "adapter_smoke_full"), start=1
        ):
            amount = Decimal("99000") + Decimal(index) / Decimal("100")
            source = rollouts / source_id
            (source / ".runner").mkdir(parents=True)
            (source / ".runner" / "profile.json").write_text(
                json.dumps(profile_document(
                    initial_cash=amount,
                    cohort="official_claude_v2",
                    predecessor="old",
                )) + "\n",
                encoding="utf-8",
            )
            StateStore(source / ".broker").initialize(amount, occurred_at=NOW)
            values[source_id] = amount
        return values

    def test_preview_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, rollouts = self.project(Path(directory))
            self.sources(rollouts)
            result = prepare(
                project_root=project,
                rollouts_root=rollouts,
                source_set="official_claude_v2",
                target_set="adapter_smoke_full",
                execute=False,
            )
            self.assertFalse(result["mutated"])
            self.assertEqual(len(result["rollouts"]), 15)
            self.assertFalse(any(rollouts.glob("adapter_smoke_full_*")))

    def test_execute_creates_disposable_clean_isolated_accounts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, rollouts = self.project(Path(directory))
            values = self.sources(rollouts)
            result = prepare(
                project_root=project,
                rollouts_root=rollouts,
                source_set="official_claude_v2",
                target_set="adapter_smoke_full",
                execute=True,
            )
            self.assertTrue(result["mutated"])
            for source_id, target_id, _ in rollout_pairs(
                "official_claude_v2", "adapter_smoke_full"
            ):
                target = rollouts / target_id
                profile = load_profile(target)
                state = StateStore(target / ".broker").load()
                self.assertTrue(profile.overnight_smoke_until_next_noon)
                self.assertEqual(profile.initial_cash, values[source_id])
                self.assertEqual(state.cash_total, values[source_id])
                self.assertEqual(state.positions, ())
                self.assertIsNone(state.open_plan)
                self.assertFalse((target / ".runner" / "session.json").exists())
                self.assertTrue((target / ".runner" / "SMOKE.json").is_file())
                rules = (target / "workspace" / "BROKER.md").read_text()
                self.assertIn("隔离 smoke 临时覆盖", rules)
                launcher = (target / "workspace" / "broker").read_text()
                self.assertIn(
                    "export BROKER_OVERNIGHT_SMOKE_UNTIL_NEXT_NOON=1",
                    launcher,
                )


if __name__ == "__main__":
    unittest.main()
