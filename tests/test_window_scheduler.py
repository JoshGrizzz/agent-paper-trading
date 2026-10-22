from pathlib import Path
import sys
import tempfile
import unittest

from trading_runner.window_scheduler import (
    MODEL_CONFIGS,
    WorkerSpec,
    _run_wave,
    build_wave_specs,
    resolve_models,
    rollout_order,
)


class WindowSchedulerTests(unittest.TestCase):
    def test_rollout_order_rotates_across_windows(self) -> None:
        self.assertEqual(rollout_order(1), (1, 2, 3, 4, 5))
        self.assertEqual(rollout_order(2), (2, 3, 4, 5, 1))
        self.assertEqual(rollout_order(5), (5, 1, 2, 3, 4))
        self.assertEqual(rollout_order(6), (1, 2, 3, 4, 5))
        with self.assertRaises(ValueError):
            rollout_order(0)

    def test_codex_builds_five_five_wide_barrier_waves(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            waves = build_wave_specs(
                harness="codex",
                rollout_set="official_codex",
                window_index=2,
                models=MODEL_CONFIGS["codex"],
                reasoning_effort="high",
                timeout=900,
                as_of=None,
                batch_directory=root / "batch",
                project_root=root,
                python_executable="python-test",
            )

        self.assertEqual(len(waves), 5)
        self.assertTrue(all(len(wave) == 5 for wave in waves))
        self.assertEqual([wave[0].rollout_number for wave in waves], [2, 3, 4, 5, 1])
        self.assertEqual(len({spec.rollout_id for wave in waves for spec in wave}), 25)
        self.assertEqual(
            waves[0][0].rollout_id,
            "official_codex_1_gpt-5_6-sol_r02",
        )
        self.assertEqual(waves[0][0].command[0], "python-test")
        self.assertEqual(waves[0][0].conversation, "new")
        self.assertEqual(waves[0][-1].model, "gpt-6-astra")

    def test_claude_builds_five_three_wide_waves_and_resumes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session = (
                root
                / "rollouts"
                / "official_claude_1_opus_r01"
                / ".runner"
                / "session.json"
            )
            session.parent.mkdir(parents=True)
            session.write_text("{}", encoding="utf-8")
            waves = build_wave_specs(
                harness="claude",
                rollout_set="official_claude",
                window_index=1,
                models=MODEL_CONFIGS["claude"],
                reasoning_effort="high",
                timeout=900,
                as_of="2026-10-20T08:30:00-04:00",
                batch_directory=root / "batch",
                project_root=root,
            )

        self.assertEqual(len(waves), 5)
        self.assertTrue(all(len(wave) == 3 for wave in waves))
        self.assertEqual(waves[0][0].conversation, "resume")
        self.assertIn("--as-of", waves[0][0].command)
        self.assertEqual(len({spec.rollout_id for wave in waves for spec in wave}), 15)

    def test_zcode_builds_five_strictly_sequential_waves(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            waves = build_wave_specs(
                harness="zcode",
                rollout_set="pilot_zcode01",
                window_index=1,
                models=MODEL_CONFIGS["zcode"],
                reasoning_effort="high",
                timeout=900,
                as_of=None,
                batch_directory=root / "batch",
                project_root=root,
            )

        self.assertEqual(len(waves), 5)
        self.assertTrue(all(len(wave) == 1 for wave in waves))
        self.assertEqual([wave[0].rollout_number for wave in waves], [1, 2, 3, 4, 5])
        self.assertEqual(len({wave[0].rollout_id for wave in waves}), 5)
        self.assertTrue(all(wave[0].model == "GLM-5.3" for wave in waves))

    def test_model_override_preserves_fixed_width_and_distinctness(self) -> None:
        self.assertEqual(
            resolve_models("claude", "opus-v1,sonnet-v1,haiku-v1"),
            ("opus-v1", "sonnet-v1", "haiku-v1"),
        )
        with self.assertRaises(ValueError):
            resolve_models("claude", "opus,sonnet")
        with self.assertRaises(ValueError):
            resolve_models("claude", "sonnet,sonnet,sonnet")

    def test_wave_collects_runner_results(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            specs = []
            for index in (1, 2):
                specs.append(
                    WorkerSpec(
                        wave=1,
                        rollout_number=1,
                        model_index=index,
                        model=f"model-{index}",
                        rollout_id=f"rollout-{index}",
                        command=(
                            sys.executable,
                            "-c",
                            "import json; print(json.dumps({'ok': True, 'run_id': 'run'}))",
                        ),
                        log_path=root / f"{index}.log",
                        conversation="new",
                    )
                )

            results, passed = _run_wave(specs, timeout=5)

        self.assertTrue(passed)
        self.assertEqual(len(results), 2)
        self.assertTrue(all(result["ok"] for result in results))
        self.assertEqual([result["model_index"] for result in results], [1, 2])


if __name__ == "__main__":
    unittest.main()
