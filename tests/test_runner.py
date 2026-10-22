from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from zoneinfo import ZoneInfo

from trading_runner.agent_client import AgentResult
from trading_runner.runner import (
    BrokerResult,
    RunConfig,
    RunnerError,
    _rollout_lock,
    build_environment,
    build_prompt,
    initialize_rollout,
    run_once,
    validate_decision_record,
)


ET = ZoneInfo("America/New_York")
NOW = datetime(2026, 10, 20, 8, 0, tzinfo=ET)
SESSION_ID = "01a156b0-e2ea-7582-a0f3-dba8d9b3786a"


def decision_record() -> str:
    return f"""## {NOW.isoformat()}

### 本轮判断

- 市场与关键信息：测试
- 当前策略及主要理由：测试
- 主要风险：测试

### 资金与持仓检查

- `cash.available`：100000.00
- 主方案买入资金需求：0.00
- Backup 1 买入资金需求：0.00
- Backup 2 买入资金需求：0.00
- 预计冻结现金：0.00
- 卖出数量检查：是

### 本轮操作

- 不操作：
  - 原因：测试

### 后续计划

- 下轮重点检查：测试
- 改变当前判断的条件：测试
"""


class FakeAgent:
    harness = "codex"

    def __init__(
        self,
        *,
        tamper: bool = False,
        tamper_rule: bool = False,
    ) -> None:
        self.tamper = tamper
        self.tamper_rule = tamper_rule
        self.calls = 0
        self.received_session_ids = []
        self.received_allow_search = []

    def version(self) -> str:
        return "fake-1"

    def invoke(self, **arguments) -> AgentResult:
        self.calls += 1
        self.received_session_ids.append(arguments["session_id"])
        self.received_allow_search.append(arguments["allow_search"])
        if self.tamper:
            path = arguments["workdir"] / "DECISIONS.md"
            path.write_text("tampered", encoding="utf-8")
        if self.tamper_rule:
            path = arguments["workdir"] / "BROKER.md"
            path.chmod(0o644)
            path.write_text("tampered", encoding="utf-8")
        return AgentResult(
            final_response=decision_record(),
            stdout="raw events",
            stderr="",
            returncode=0,
            duration_seconds=1.0,
            command=("fake-agent",),
            session_id=SESSION_ID,
        )


class TimeoutAgent(FakeAgent):
    def invoke(self, **arguments) -> AgentResult:
        event = json.dumps({"type": "thread.started", "thread_id": SESSION_ID})
        raise subprocess.TimeoutExpired(
            cmd=("fake-agent",),
            timeout=1,
            output=event + "\n",
            stderr="timed out",
        )


class FailedAgent(FakeAgent):
    harness = "zcode"

    def invoke(self, **arguments) -> AgentResult:
        return AgentResult(
            final_response="",
            stdout="",
            stderr=(
                "[project-access-token] code: project_token_login_failed\n"
                "Error: Turn execution failed\n"
            ),
            returncode=1,
            duration_seconds=1.0,
            command=("fake-agent",),
            session_id=None,
        )


class MutatingInvalidAgent(FakeAgent):
    def invoke(self, **arguments) -> AgentResult:
        broker_directory = arguments["workdir"] / ".broker"
        (broker_directory / "state.json").write_text(
            "agent state", encoding="utf-8"
        )
        (broker_directory / "ledger.jsonl").write_text(
            "agent ledger\n", encoding="utf-8"
        )
        return AgentResult(
            final_response="invalid decision record",
            stdout="raw events",
            stderr="",
            returncode=0,
            duration_seconds=1.0,
            command=("fake-agent",),
            session_id=SESSION_ID,
        )


class HarnessFakeAgent(FakeAgent):
    def __init__(self, harness: str, session_id: str) -> None:
        super().__init__()
        self.harness = harness
        self.session_id = session_id

    def invoke(self, **arguments) -> AgentResult:
        self.calls += 1
        self.received_session_ids.append(arguments["session_id"])
        self.received_allow_search.append(arguments["allow_search"])
        return AgentResult(
            final_response=decision_record(),
            stdout="raw events",
            stderr="",
            returncode=0,
            duration_seconds=1.0,
            command=("fake-agent",),
            session_id=self.session_id,
        )


class FakeBroker:
    def __init__(self) -> None:
        self.commands = []

    def __call__(self, workdir, command, environment, as_of, timeout):
        self.commands.append(command)
        document = {
            "ok": True,
            "command": command,
            "settled": False,
            "fills": [],
            "account": {"cash": {"available": "100000.00"}},
            "positions": [],
            "open_plans": [],
        }
        return BrokerResult(document, "{}", "", 0)


class PersistentFakeBroker(FakeBroker):
    def __call__(self, workdir, command, environment, as_of, timeout):
        if command == "settle":
            broker_directory = workdir / ".broker"
            (broker_directory / "state.json").write_text(
                "settled state", encoding="utf-8"
            )
            (broker_directory / "ledger.jsonl").write_text(
                "settlement event\n", encoding="utf-8"
            )
        return super().__call__(workdir, command, environment, as_of, timeout)


class RunnerTests(unittest.TestCase):
    def project(self, root: Path) -> Path:
        (root / "templates").mkdir()
        (root / "BROKER.md").write_text("broker", encoding="utf-8")
        (root / "universe.txt").write_text("SPY\n", encoding="utf-8")
        (root / "templates" / "DECISION_FORMAT.md").write_text(
            "format", encoding="utf-8"
        )
        (root / "templates" / "DECISIONS.md").write_text(
            "# 决策历史\n", encoding="utf-8"
        )
        (root / "broker").write_text(
            "import json, os, sys\n"
            "print(json.dumps({'argv': sys.argv[1:], 'as_of_env': os.environ.get('BROKER_AS_OF'), 'data_dir': os.environ.get('BROKER_DATA_DIR')}))\n",
            encoding="utf-8",
        )
        return root

    def config(self, project: Path) -> RunConfig:
        return RunConfig(
            "rollout_01",
            "codex",
            "fake-model",
            NOW,
            project_root=project,
        )

    def test_validates_exactly_one_decision_record(self) -> None:
        expected = decision_record().strip()
        self.assertEqual(validate_decision_record(decision_record(), NOW), expected)
        self.assertEqual(
            validate_decision_record("已完成操作。\n\n" + decision_record(), NOW),
            expected,
        )
        with self.assertRaises(RunnerError):
            validate_decision_record(
                decision_record() + "\n## 2026-10-19T09:00:00-04:00\n",
                NOW,
            )
        normalized = validate_decision_record(
            decision_record().replace("08:00", "09:00", 1), NOW
        )
        self.assertTrue(normalized.startswith(f"## {NOW.isoformat()}\n"))
        with self.assertRaises(RunnerError):
            validate_decision_record(
                decision_record().replace(NOW.isoformat(), "not-a-timestamp", 1),
                NOW,
            )
        with self.assertRaises(RunnerError):
            validate_decision_record(
                decision_record().replace(
                    NOW.isoformat(), "2026-10-20T08:00:00", 1
                ),
                NOW,
            )

    def test_restores_only_a_complete_decision_body_missing_its_heading(self) -> None:
        body = decision_record().split("\n", 2)[2]
        normalized = validate_decision_record(body, NOW)
        self.assertEqual(normalized, decision_record().strip())

        with self.assertRaisesRegex(
            RunnerError,
            "exactly one decision record",
        ):
            validate_decision_record(
                body.replace("### 后续计划", "后续计划", 1),
                NOW,
            )

        with self.assertRaisesRegex(
            RunnerError,
            "exactly one decision record",
        ):
            validate_decision_record("说明文字\n\n" + body, NOW)

    def test_prompt_injects_the_authoritative_dynamic_heading(self) -> None:
        prompt = build_prompt(NOW)
        self.assertIn(
            f"本轮最终回复的第一行必须严格为：\n## {NOW.isoformat()}\n",
            prompt,
        )
        self.assertIn("可以使用 sed 等只读命令读取这四个文件", prompt)
        self.assertIn("必须明确包含 `提交交易方案`、`撤销交易方案` 或 `不操作`", prompt)

    def test_normalizes_final_section_list_label(self) -> None:
        malformed = decision_record().replace(
            "### 后续计划",
            "- 后续计划：",
        )
        normalized = validate_decision_record(malformed, NOW)
        self.assertIn("\n### 后续计划\n", normalized)
        self.assertNotIn("\n- 后续计划：\n", normalized)

    def test_decision_timestamp_is_always_normalized_to_runner_time(self) -> None:
        started = NOW.replace(microsecond=250000)
        completed = NOW.replace(minute=2)
        truncated = decision_record().replace(
            NOW.isoformat(), NOW.isoformat(timespec="seconds"), 1
        )
        normalized = validate_decision_record(
            truncated,
            started,
            frozen_time=False,
            completed_at=completed,
        )
        self.assertTrue(normalized.startswith(f"## {started.isoformat()}\n"))

        later = decision_record().replace(
            NOW.isoformat(), NOW.replace(minute=1).isoformat(), 1
        )
        normalized = validate_decision_record(
            later,
            started,
            frozen_time=False,
            completed_at=completed,
        )
        self.assertTrue(normalized.startswith(f"## {started.isoformat()}\n"))

        stale = decision_record().replace(
            NOW.isoformat(), NOW.replace(hour=7, minute=24, second=10).isoformat(), 1
        )
        normalized = validate_decision_record(
            stale,
            started,
            frozen_time=False,
            completed_at=completed,
        )
        self.assertTrue(normalized.startswith(f"## {started.isoformat()}\n"))

        future = decision_record().replace(
            NOW.isoformat(), NOW.replace(minute=3).isoformat(), 1
        )
        normalized = validate_decision_record(
            future,
            started,
            frozen_time=False,
            completed_at=completed,
        )
        self.assertTrue(normalized.startswith(f"## {started.isoformat()}\n"))

    def test_only_explicit_test_runs_freeze_agent_broker_time(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(Path(directory))
            real_config = self.config(project)
            self.assertEqual(build_environment(real_config)["BROKER_AS_OF"], "")
            frozen_config = RunConfig(
                "rollout_01",
                "codex",
                "fake-model",
                NOW,
                project_root=project,
                frozen_time=True,
            )
            self.assertEqual(
                build_environment(frozen_config)["BROKER_AS_OF"],
                NOW.isoformat(),
            )

            live_rollout = initialize_rollout(real_config)
            for name, expected in (
                ("BROKER.md", b"broker"),
                ("universe.txt", b"SPY\n"),
                ("DECISION_FORMAT.md", b"format"),
            ):
                snapshot = live_rollout / name
                self.assertFalse(snapshot.is_symlink())
                self.assertEqual(snapshot.read_bytes(), expected)
                self.assertEqual(snapshot.stat().st_mode & 0o222, 0)
            live_launcher = (live_rollout / "broker").read_text(encoding="utf-8")
            self.assertIn("export BROKER_DATA_DIR=", live_launcher)
            self.assertIn("export BROKER_MARKET_CACHE=", live_launcher)
            self.assertIn("export BROKER_UNIVERSE=", live_launcher)
            self.assertIn("unset BROKER_AS_OF", live_launcher)
            self.assertNotIn(" --as-of ", live_launcher)

            frozen_rollout = initialize_rollout(frozen_config)
            frozen_launcher = (frozen_rollout / "broker").read_text(encoding="utf-8")
            self.assertIn(" --as-of ", frozen_launcher)
            self.assertIn(NOW.isoformat(), frozen_launcher)

            completed = subprocess.run(
                [str(frozen_rollout / "broker"), "status", "--json"],
                text=True,
                capture_output=True,
                env={**os.environ, "BROKER_AS_OF": "2099-01-01T00:00:00-05:00"},
                check=True,
            )
            invocation = json.loads(completed.stdout)
            self.assertIsNone(invocation["as_of_env"])
            self.assertEqual(invocation["argv"][-2:], ["--as-of", NOW.isoformat()])
            self.assertEqual(
                invocation["data_dir"],
                str(frozen_rollout / ".broker"),
            )

    def test_run_once_appends_record_and_logs_all_stages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(self.project(Path(directory)))
            broker = FakeBroker()
            agent = FakeAgent()
            result = run_once(config, agent_client=agent, broker_call=broker)
            self.assertTrue(result["ok"])
            self.assertEqual(broker.commands, ["settle", "status", "status"])
            self.assertEqual(agent.calls, 1)
            self.assertEqual(agent.received_session_ids, [None])
            self.assertEqual(agent.received_allow_search, [True])
            self.assertEqual(result["codex_session_id"], SESSION_ID)
            session = json.loads(
                (config.rollout_directory / ".runner" / "session.json").read_text()
            )
            self.assertEqual(session["session_id"], SESSION_ID)
            decisions = (config.rollout_directory / "DECISIONS.md").read_text(
                encoding="utf-8"
            )
            self.assertIn(decision_record().strip(), decisions)
            log = Path(result["log_directory"])
            for name in (
                "metadata.json",
                "prompt.txt",
                "settle.json",
                "pre_status.json",
                "agent_stdout.log",
                "agent_final.md",
                "post_status.json",
                "summary.json",
            ):
                self.assertTrue((log / name).is_file(), name)

    def test_second_turn_resumes_the_same_codex_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(self.project(Path(directory)))
            agent = FakeAgent()
            run_once(config, agent_client=agent, broker_call=FakeBroker())
            result = run_once(config, agent_client=agent, broker_call=FakeBroker())
            self.assertEqual(
                agent.received_session_ids,
                [None, SESSION_ID],
            )
            self.assertTrue(result["session_resumed"])

    def test_all_native_harnesses_resume_their_exact_session(self) -> None:
        cases = (
            ("claude", "b2027781-90ce-4270-9bf6-75df881fd803"),
            ("dsh", "session-test"),
            ("zcode", "sess_test"),
        )
        for harness, session_id in cases:
            with self.subTest(harness=harness):
                with tempfile.TemporaryDirectory() as directory:
                    project = self.project(Path(directory))
                    config = RunConfig(
                        "rollout_01",
                        harness,
                        "configured-model",
                        NOW,
                        project_root=project,
                    )
                    agent = HarnessFakeAgent(harness, session_id)
                    run_once(config, agent_client=agent, broker_call=FakeBroker())
                    result = run_once(
                        config,
                        agent_client=agent,
                        broker_call=FakeBroker(),
                    )
                    self.assertEqual(
                        agent.received_session_ids,
                        [None, session_id],
                    )
                    self.assertEqual(result["session_id"], session_id)
                    self.assertTrue(result["session_resumed"])
                    session = json.loads(
                        (
                            config.rollout_directory
                            / ".runner"
                            / "session.json"
                        ).read_text()
                    )
                    self.assertEqual(session["harness"], harness)
                    self.assertEqual(session["session_id"], session_id)

    def test_rollout_cannot_switch_harness_after_session_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(Path(directory))
            dsh_config = RunConfig(
                "rollout_01",
                "dsh",
                "configured-model",
                NOW,
                project_root=project,
            )
            run_once(
                dsh_config,
                agent_client=HarnessFakeAgent("dsh", "session-test"),
                broker_call=FakeBroker(),
            )
            zcode_config = RunConfig(
                "rollout_01",
                "zcode",
                "configured-model",
                NOW,
                project_root=project,
            )
            with self.assertRaises(RunnerError):
                run_once(
                    zcode_config,
                    agent_client=HarnessFakeAgent("zcode", "sess_test"),
                    broker_call=FakeBroker(),
                )

    def test_frozen_turn_disables_agent_search(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(Path(directory))
            config = RunConfig(
                "rollout_01",
                "codex",
                "fake-model",
                NOW,
                project_root=project,
                frozen_time=True,
            )
            agent = FakeAgent()
            result = run_once(config, agent_client=agent, broker_call=FakeBroker())
            self.assertEqual(agent.received_allow_search, [False])
            metadata = json.loads(
                (Path(result["log_directory"]) / "metadata.json").read_text()
            )
            self.assertFalse(metadata["search_enabled"])
            prompt = (Path(result["log_directory"]) / "prompt.txt").read_text(
                encoding="utf-8"
            )
            self.assertIn("不得尝试联网搜索", prompt)

    def test_timeout_preserves_reported_codex_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(self.project(Path(directory)))
            with self.assertRaises(RunnerError):
                run_once(
                    config,
                    agent_client=TimeoutAgent(),
                    broker_call=FakeBroker(),
                )
            session = json.loads(
                (config.rollout_directory / ".runner" / "session.json").read_text()
            )
            self.assertEqual(session["session_id"], SESSION_ID)

    def test_nonzero_agent_exit_reports_stderr_before_missing_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(Path(directory))
            config = RunConfig(
                "rollout_01",
                "zcode",
                "GLM-5.3",
                NOW,
                project_root=project,
            )
            with self.assertRaisesRegex(
                RunnerError,
                "project_token_login_failed",
            ):
                run_once(
                    config,
                    agent_client=FailedAgent(),
                    broker_call=FakeBroker(),
                )

    def test_invalid_decision_rolls_back_agent_broker_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(self.project(Path(directory)))
            rollout = initialize_rollout(config)
            decisions_before = (rollout / "DECISIONS.md").read_bytes()

            with self.assertRaisesRegex(
                RunnerError,
                "exactly one decision record",
            ):
                run_once(
                    config,
                    agent_client=MutatingInvalidAgent(),
                    broker_call=PersistentFakeBroker(),
                )

            self.assertEqual(
                (rollout / ".broker" / "state.json").read_text(encoding="utf-8"),
                "settled state",
            )
            self.assertEqual(
                (rollout / ".broker" / "ledger.jsonl").read_text(encoding="utf-8"),
                "settlement event\n",
            )
            self.assertEqual(
                (rollout / "DECISIONS.md").read_bytes(), decisions_before
            )
            failures = sorted((rollout / ".runner" / "logs").glob("*/failure.json"))
            failure = json.loads(failures[-1].read_text(encoding="utf-8"))
            self.assertTrue(failure["broker_rolled_back"])
            self.assertEqual(
                failure["restored_broker_files"],
                ["state.json", "ledger.jsonl"],
            )
            self.assertEqual(failure["rollback_errors"], [])


    def test_same_rollout_cannot_run_concurrently(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(self.project(Path(directory)))
            rollout = initialize_rollout(config)
            with _rollout_lock(rollout):
                with self.assertRaises(RunnerError):
                    run_once(
                        config,
                        agent_client=FakeAgent(),
                        broker_call=FakeBroker(),
                    )


    def test_agent_cannot_modify_decision_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(self.project(Path(directory)))
            rollout = initialize_rollout(config)
            original = (rollout / "DECISIONS.md").read_bytes()
            with self.assertRaises(RunnerError):
                run_once(
                    config,
                    agent_client=FakeAgent(tamper=True),
                    broker_call=FakeBroker(),
                )
            self.assertEqual((rollout / "DECISIONS.md").read_bytes(), original)

    def test_agent_cannot_modify_rule_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(self.project(Path(directory)))
            rollout = initialize_rollout(config)
            rule = rollout / "BROKER.md"
            original = rule.read_bytes()
            with self.assertRaises(RunnerError):
                run_once(
                    config,
                    agent_client=FakeAgent(tamper_rule=True),
                    broker_call=FakeBroker(),
                )
            self.assertEqual(rule.read_bytes(), original)
            self.assertEqual(rule.stat().st_mode & 0o222, 0)


if __name__ == "__main__":
    unittest.main()
