from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "install.py"
spec = importlib.util.spec_from_file_location("aios_install", MODULE_PATH)
assert spec is not None and spec.loader is not None
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

HOOK_PATH = Path(__file__).resolve().parents[1] / ".codex" / "hooks" / "session_start.py"
hook_spec = importlib.util.spec_from_file_location("aios_session_start", HOOK_PATH)
assert hook_spec is not None and hook_spec.loader is not None
session_start = importlib.util.module_from_spec(hook_spec)
hook_spec.loader.exec_module(session_start)


class InstallerSafetyTest(unittest.TestCase):
    """What: 再インストールで既存バックアップと無関係なhookを保持する。"""

    def test_backup_path_does_not_overwrite_existing_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "knowledge-first"
            target.mkdir()
            (Path(directory) / "knowledge-first.pre-aios-backup").mkdir()
            backup = installer.next_backup_path(target)
            self.assertEqual("knowledge-first.pre-aios-backup-1", backup.name)

    def test_remove_aios_commands_keeps_unrelated_handler_in_same_group(self) -> None:
        hooks = {
            "SessionStart": [
                {
                    "hooks": [
                        {"type": "command", "command": "echo unrelated"},
                        {"type": "command", "command": "python C:\\repo\\session_start.py"},
                    ]
                }
            ]
        }
        installer.remove_aios_commands(hooks, "C:\\repo\\session_start.py")
        self.assertEqual(1, len(hooks["SessionStart"]))
        self.assertEqual("echo unrelated", hooks["SessionStart"][0]["hooks"][0]["command"])


    def test_session_start_context_includes_shared_engineering_guidance(self) -> None:
        context = session_start.build_context(Path("C:/sora-ai-os"), pending=0)
        self.assertIn("# Simple Engineering", context)
        self.assertIn("Avoid reinventing the wheel", context)
        self.assertIn("request_user_input", context)
        self.assertIn("Keep only necessary changes", context)
        self.assertIn("# Implementation Harness", context)
        self.assertIn("one reusable test unit per feature", context)
        self.assertIn("opened pull request", context)

if __name__ == "__main__":
    unittest.main()
