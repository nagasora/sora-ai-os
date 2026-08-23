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


if __name__ == "__main__":
    unittest.main()
