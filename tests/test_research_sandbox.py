from pathlib import Path
import tempfile
import unittest
from unittest.mock import call, patch

from trading_runner.research_sandbox import _bind_read_only_directory


class ResearchSandboxTests(unittest.TestCase):
    def test_zoneinfo_directory_is_bound_read_only(self) -> None:
        source = Path("/usr/share/zoneinfo")
        if not source.is_dir():
            self.skipTest("host timezone database is unavailable")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "usr" / "share" / "zoneinfo"
            with patch("trading_runner.research_sandbox._mount") as mount:
                _bind_read_only_directory(root, str(source))

            self.assertTrue(target.is_dir())
            self.assertEqual(
                mount.call_args_list,
                [
                    call("--bind", str(source), str(target)),
                    call("-o", "remount,bind,ro", str(target)),
                ],
            )


if __name__ == "__main__":
    unittest.main()
