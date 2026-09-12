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

    def test_agent_tree_install_preserves_settings_and_is_idempotent(self) -> None:
        """モデルと禁止方針だけを移行し、再適用と無関係な設定を保証する。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home = root / "home"
            project = root / "project"
            config_dir = project / ".codex"
            config_dir.mkdir(parents=True)
            misplaced = config_dir / "agents" / "config.toml"
            misplaced.parent.mkdir()
            misplaced.write_text("[features]\nmulti_agent = false\n", encoding="utf-8")
            config = config_dir / "config.toml"
            config.write_text(
                '# project setting\nmodel = "old"\nmodel_reasoning_effort = "mid"\n'
                '[windows]\nsandbox = "unelevated"\n'
                '[features]\nmulti_agent = false\nmemories = true\n',
                encoding="utf-8",
            )
            instructions = project / "AGENTS.md"
            instructions.write_text(
                "# Project\n\n## Single-agent policy\n\n"
                "- Codex subagents are prohibited by default.\n\n"
                "## Testing\nKeep the existing test command.\n",
                encoding="utf-8",
            )
            repo = MODULE_PATH.parents[1]
            plan = installer.plan_agent_tree(repo, home, [project])
            self.assertFalse((home / ".codex").exists())
            self.assertIsNone(plan[misplaced.resolve()])
            parsed = installer.tomllib.loads(plan[config.resolve()])
            self.assertEqual("gpt-6-astra", parsed["model"])
            self.assertEqual("medium", parsed["model_reasoning_effort"])
            self.assertTrue(parsed["features"]["multi_agent"])
            self.assertTrue(parsed["features"]["memories"])
            self.assertEqual("unelevated", parsed["windows"]["sandbox"])
            self.assertEqual(3, parsed["agents"]["max_concurrent_threads_per_session"])
            self.assertNotIn("prohibited", plan[instructions.resolve()])
            self.assertIn("Keep the existing test command.", plan[instructions.resolve()])
            expected = {
                "explorer": ("gpt-5.6-luna", "max"),
                "worker": ("gpt-5.6-sol", "high"),
                "researcher": ("gpt-5.6-luna", "max"),
                "reviewer": ("gpt-6-astra", "xhigh"),
            }
            for name, (model, effort) in expected.items():
                role = installer.tomllib.loads(plan[home.resolve() / ".codex" / "agents" / f"{name}.toml"])
                self.assertEqual(name, role["name"])
                self.assertEqual((model, effort), (role["model"], role["model_reasoning_effort"]))
                if name != "worker":
                    self.assertEqual("read-only", role["sandbox_mode"])
            for target, content in plan.items():
                if content is None:
                    target.unlink()
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(content, encoding="utf-8")
            self.assertEqual(
                {target: text for target, text in plan.items() if text is not None},
                installer.plan_agent_tree(repo, home, [project]),
            )
            config.write_text("[broken", encoding="utf-8")
            with self.assertRaises(installer.tomllib.TOMLDecodeError):
                installer.plan_agent_tree(repo, home, [project])


if __name__ == "__main__":
    unittest.main()
