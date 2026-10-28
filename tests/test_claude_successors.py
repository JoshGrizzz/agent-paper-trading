from datetime import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from trading_broker.state_store import StateStore
from trading_runner.agent_client import AgentResult, ClaudeClient
from trading_runner.claude_successors import execute, preview, rollout_pairs
from trading_runner.rollout_profile import profile_document
from trading_runner.runner import BrokerResult, RunConfig, RunnerError, run_once


ET = ZoneInfo("America/New_York")
NOW = datetime(2026, 10, 27, 20, 5, tzinfo=ET)


class SuccessorTests(unittest.TestCase):
    def project(self, root: Path) -> tuple[Path, Path]:
        (root / "templates").mkdir()
        (root / "rollouts").mkdir()
        (root / "BROKER.md").write_text(
            "# Rules\n\n- 初始现金为 100,000 美元，所有金额以美元计。\n",
            encoding="utf-8",
        )
        (root / "universe.txt").write_text("SPY\n", encoding="utf-8")
        (root / "templates" / "DECISION_FORMAT.md").write_text("format", encoding="utf-8")
        (root / "templates" / "DECISIONS.md").write_text("# decisions\n", encoding="utf-8")
        (root / "broker").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
        (root / "broker").chmod(0o755)
        return root, root / "rollouts"

    def sources(self, rollouts: Path) -> dict[str, Decimal]:
        equities = {}
        for index, (source_id, _, _) in enumerate(
            rollout_pairs("official_claude", "official_claude_v2"), start=1
        ):
            directory = rollouts / source_id
            (directory / ".runner").mkdir(parents=True)
            amount = Decimal("100000.0000") + Decimal(index) / Decimal("10000")
            StateStore(directory / ".broker").initialize(amount, occurred_at=NOW)
            equities[source_id] = amount
        return equities

    def tree_hash(self, root: Path) -> str:
        digest = hashlib.sha256()
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            digest.update(str(path.relative_to(root)).encode())
            digest.update(path.read_bytes())
        return digest.hexdigest()

    def broker_result(self, workdir: Path, command: str, *args) -> BrokerResult:
        state = StateStore(workdir / ".broker").load()
        document = {
            "ok": True, "command": command, "fills": [],
            "open_plans": [], "account": {"equity": str(state.cash_total)},
        }
        return BrokerResult(document, "{}", "", 0)

    def test_preview_is_read_only_and_creates_no_targets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, rollouts = self.project(Path(directory))
            self.sources(rollouts)
            before = self.tree_hash(project)
            result = preview(
                project_root=project, rollouts_root=rollouts,
                source_set="official_claude", target_set="official_claude_v2",
                as_of=NOW,
            )
            self.assertFalse(result["mutated"])
            self.assertEqual(len(result["rollouts"]), 15)
            self.assertEqual(before, self.tree_hash(project))
            self.assertFalse(any(rollouts.glob("official_claude_v2_*")))

    def test_execute_creates_clean_exact_cash_successors_and_archives_sources(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, rollouts = self.project(Path(directory))
            equities = self.sources(rollouts)
            with patch(
                "trading_runner.claude_successors.run_broker",
                side_effect=self.broker_result,
            ):
                result = execute(
                    project_root=project, rollouts_root=rollouts,
                    source_set="official_claude", target_set="official_claude_v2",
                    as_of=NOW,
                )
            self.assertEqual(len(result["rollouts"]), 15)
            for source_id, target_id, _ in rollout_pairs(
                "official_claude", "official_claude_v2"
            ):
                target = rollouts / target_id
                state = StateStore(target / ".broker").load()
                self.assertEqual(state.initial_cash, equities[source_id])
                self.assertEqual(state.cash_total, equities[source_id])
                self.assertEqual(state.positions, ())
                self.assertIsNone(state.open_plan)
                self.assertFalse((target / ".runner" / "session.json").exists())
                self.assertTrue((target / "DECISIONS.md").is_symlink())
                self.assertEqual((target / "DECISIONS.md").resolve(), target / "workspace" / "DECISIONS.md")
                self.assertIn(str(equities[source_id]), (target / "workspace" / "BROKER.md").read_text())
                self.assertTrue((rollouts / source_id / ".runner" / "ARCHIVED.json").is_file())
            manifest = json.loads((project / "cohorts" / "official_claude_v2.json").read_text())
            self.assertEqual(manifest["handoff_as_of"], NOW.isoformat())
            self.assertEqual(len({row["handoff_as_of"] for row in manifest["rollouts"]}), 1)

    def test_open_plan_aborts_entire_batch_without_targets_or_archives(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, rollouts = self.project(Path(directory))
            self.sources(rollouts)
            first_source = rollout_pairs("official_claude", "official_claude_v2")[0][0]

            def blocked(workdir, command, *args):
                result = self.broker_result(workdir, command, *args)
                if command == "status" and workdir.name == first_source:
                    result.document["open_plans"] = [{"plan_id": "pending"}]
                return result

            with patch("trading_runner.claude_successors.run_broker", side_effect=blocked):
                with self.assertRaises(RunnerError):
                    execute(
                        project_root=project, rollouts_root=rollouts,
                        source_set="official_claude", target_set="official_claude_v2",
                        as_of=NOW,
                    )
            self.assertFalse(any(rollouts.glob("official_claude_v2_*")))
            self.assertFalse(any(rollouts.glob("official_claude_*/.runner/ARCHIVED.json")))

    def test_archived_rollout_is_not_runnable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, rollouts = self.project(Path(directory))
            rollout = rollouts / "old"
            (rollout / ".runner").mkdir(parents=True)
            (rollout / ".runner" / "ARCHIVED.json").write_text("{}\n")
            config = RunConfig(
                "old", "claude", "opus", NOW,
                project_root=project, rollouts_root=rollouts,
            )
            with self.assertRaisesRegex(RunnerError, "ARCHIVED"):
                run_once(config)

    def test_python_permission_is_v2_opt_in(self) -> None:
        client = ClaudeClient("claude-test")
        old = client.build_command(
            model="opus", reasoning_effort="high", session_id=None,
            allow_isolated_python=False,
        )
        new = client.build_command(
            model="opus", reasoning_effort="high", session_id=None,
            allow_isolated_python=True,
        )
        old_allowed = old[old.index("--allowedTools") + 1]
        new_allowed = new[new.index("--allowedTools") + 1]
        self.assertNotIn("Bash(python3 *)", old_allowed)
        self.assertIn("Bash(python3 *)", new_allowed)
        self.assertIn("Bash(python *)", new_allowed)


    def test_v2_frozen_time_smoke_uses_clean_workspace_and_profile_cash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, rollouts = self.project(Path(directory))
            rollout = rollouts / "v2_smoke"
            (rollout / ".runner").mkdir(parents=True)
            (rollout / ".runner" / "profile.json").write_text(
                json.dumps(profile_document(
                    initial_cash=Decimal("100123.4567"),
                    cohort="test_v2", predecessor="old",
                )) + "\n",
                encoding="utf-8",
            )
            StateStore(rollout / ".broker").initialize(
                Decimal("100123.4567"), occurred_at=NOW
            )

            class FrozenAgent:
                harness = "claude"

                def __init__(self):
                    self.arguments = None

                def version(self):
                    return "fake"

                def invoke(self, **arguments):
                    self.arguments = arguments
                    response = f"""## {NOW.isoformat()}

### 本轮判断

- test

### 资金与持仓检查

- test

### 本轮操作

- 不操作：test

### 后续计划

- test
"""
                    return AgentResult(
                        response, "", "", 0, 0.1, ("fake",),
                        "b2027781-90ce-4270-9bf6-75df881fd803",
                    )

            agent = FrozenAgent()
            config = RunConfig(
                "v2_smoke", "claude", "opus", NOW,
                project_root=project, rollouts_root=rollouts, frozen_time=True,
            )
            with patch(
                "trading_runner.runner.run_broker", side_effect=self.broker_result
            ):
                result = run_once(config, agent_client=agent, broker_call=self.broker_result)
            self.assertTrue(result["ok"])
            self.assertEqual(agent.arguments["workdir"], rollout / "workspace")
            self.assertTrue(agent.arguments["allow_isolated_python"])
            self.assertFalse(agent.arguments["allow_search"])
            self.assertEqual(
                agent.arguments["environment"]["BROKER_INITIAL_CASH"],
                "100123.4567",
            )
            self.assertIn(
                f"## {NOW.isoformat()}",
                (rollout / "workspace" / "DECISIONS.md").read_text(),
            )


if __name__ == "__main__":
    unittest.main()
