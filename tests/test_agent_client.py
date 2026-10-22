from pathlib import Path
import unittest

from trading_runner.agent_client import (
    ClaudeClient,
    CodexClient,
    DshClient,
    ZCodeClient,
    _claude_result,
    _dsh_result,
    _zcode_result,
)


class AgentClientTests(unittest.TestCase):
    def test_codex_initial_command_is_persistent_sandboxed_and_search_enabled(self) -> None:
        command = CodexClient("codex-test").build_command(
            workdir=Path("/tmp/rollout"),
            model="gpt-test",
            reasoning_effort="high",
            session_id=None,
            final_output=Path("/tmp/final.md"),
            allow_search=True,
        )
        self.assertEqual(command[:2], ["codex-test", "--search"])
        self.assertNotIn("--ephemeral", command)
        self.assertIn("workspace-write", command)
        self.assertIn("never", command)
        self.assertIn("--json", command)
        self.assertIn("model_reasoning_effort=high", command)

    def test_codex_resume_command_targets_exact_session(self) -> None:
        session_id = "01a156b0-e2ea-7582-a0f3-dba8d9b3786a"
        command = CodexClient("codex-test").build_command(
            workdir=Path("/tmp/rollout"),
            model="gpt-test",
            reasoning_effort="high",
            session_id=session_id,
            final_output=Path("/tmp/final.md"),
            allow_search=True,
        )
        self.assertGreater(command.index("resume"), command.index("exec"))
        self.assertEqual(command[-2:], [session_id, "-"])
        self.assertIn("--sandbox", command)
        self.assertEqual(command[command.index("--sandbox") + 1], "workspace-write")
        self.assertIn("-C", command)
        self.assertEqual(command[command.index("-C") + 1], "/tmp/rollout")
        self.assertIn("model_reasoning_effort=high", command)

    def test_codex_frozen_command_disables_search(self) -> None:
        command = CodexClient("codex-test").build_command(
            workdir=Path("/tmp/rollout"),
            model="gpt-test",
            reasoning_effort="high",
            session_id=None,
            final_output=Path("/tmp/final.md"),
            allow_search=False,
        )
        self.assertNotIn("--search", command)

    def test_claude_initial_command_is_persistent_and_disables_subagents(self) -> None:
        session_id = "b2027781-90ce-4270-9bf6-75df881fd803"
        command = ClaudeClient("claude-test").build_command(
            model="claude-test-model",
            reasoning_effort="high",
            session_id=None,
            initial_session_id=session_id,
        )
        self.assertEqual(command[command.index("--effort") + 1], "high")
        self.assertNotIn("--no-session-persistence", command)
        self.assertEqual(command[command.index("--session-id") + 1], session_id)
        self.assertIn("--restricted", command)
        self.assertIn("dontAsk", command)
        allowed = command[command.index("--allowedTools") + 1]
        self.assertIn("Read", allowed)
        self.assertIn("Write", allowed)
        self.assertIn("Bash(./broker *)", allowed)
        self.assertIn("WebSearch", allowed)
        denied = command[command.index("--disallowedTools") + 1]
        self.assertIn("Agent", denied)

    def test_claude_resume_targets_exact_session_and_frozen_disables_search(self) -> None:
        session_id = "b2027781-90ce-4270-9bf6-75df881fd803"
        command = ClaudeClient("claude-test").build_command(
            model="claude-test-model",
            reasoning_effort="high",
            session_id=session_id,
            allow_search=False,
        )
        self.assertEqual(command[command.index("--resume") + 1], session_id)
        denied = command[command.index("--disallowedTools") + 1]
        self.assertIn("Agent", denied)
        self.assertIn("WebSearch", denied)
        self.assertIn("WebFetch", denied)
        allowed = command[command.index("--allowedTools") + 1]
        self.assertNotIn("WebSearch", allowed)
        self.assertNotIn("WebFetch", allowed)

    def test_dsh_command_uses_stdin_and_exact_session(self) -> None:
        initial = DshClient("dsh-test").build_command(session_id=None)
        self.assertEqual(initial, ["dsh-test", "headless", "--json", "-"])
        resumed = DshClient("dsh-test").build_command(
            session_id="session-abc"
        )
        self.assertEqual(
            resumed,
            [
                "dsh-test",
                "headless",
                "--json",
                "--session-id",
                "session-abc",
                "-",
            ],
        )

    def test_zcode_command_is_guarded_and_resumes_exact_session(self) -> None:
        command = ZCodeClient("zcode-test").build_command(
            prompt="test prompt",
            workdir=Path("/tmp/rollout"),
            session_id="sess_abc",
            allow_search=False,
        )
        self.assertEqual(command[command.index("--resume") + 1], "sess_abc")
        self.assertEqual(command[command.index("--mode") + 1], "guarded")
        self.assertEqual(
            command[command.index("--workflow-mode") + 1],
            "disabled",
        )
        denied = command[command.index("--disallowed-tools") + 1]
        self.assertIn("Agent", denied)
        self.assertIn("WebSearch", denied)
        self.assertEqual(command[-2:], ["--prompt", "test prompt"])

    def test_native_output_parsers_extract_final_and_session(self) -> None:
        claude = (
            '{"result":"claude final",'
            '"session_id":"b2027781-90ce-4270-9bf6-75df881fd803"}'
        )
        self.assertEqual(
            _claude_result(claude),
            (
                "claude final",
                "b2027781-90ce-4270-9bf6-75df881fd803",
            ),
        )
        dsh = (
            '{"type":"session","sessionId":"session-abc"}\n'
            '{"type":"final","text":"dsh final"}\n'
        )
        self.assertEqual(_dsh_result(dsh), ("dsh final", "session-abc"))
        zcode = '{"sessionId":"sess_abc","response":"zcode final"}'
        self.assertEqual(_zcode_result(zcode), ("zcode final", "sess_abc"))


if __name__ == "__main__":
    unittest.main()
