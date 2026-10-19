from __future__ import annotations

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('install_autonomy', Path(__file__).resolve().parents[1] / 'scripts/install_autonomy.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AutonomyInstallTest(unittest.TestCase):
    def test_preserves_backs_up_and_reapplies_without_changes(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()) as output:
            home = Path(directory)
            target = home / '.claude/CLAUDE.md'
            target.parent.mkdir()
            original = '# 既存の個人設定\nprivate-fixture-value\n'
            target.write_text(original, encoding='utf-8')
            self.assertEqual(2, module.install(home, False))
            self.assertFalse((home / '.codex').exists())
            self.assertEqual(2, module.install(home, True))
            self.assertTrue(target.read_text(encoding='utf-8').startswith(original))
            self.assertEqual(original, target.with_name('CLAUDE.md.pre-autonomy-backup').read_text(encoding='utf-8'))
            self.assertEqual(0, module.install(home, True))
            self.assertNotIn('private-fixture-value', output.getvalue())
            self.assertIn(str(target), output.getvalue())
            for content in (module.BEGIN, module.END + module.BEGIN, module.BEGIN * 2 + module.END):
                with self.assertRaises(ValueError):
                    module.merge(content, 'policy')
