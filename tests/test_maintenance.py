from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_maintenance.py"
spec = importlib.util.spec_from_file_location("aios_maintenance", MODULE_PATH)
assert spec is not None and spec.loader is not None
maintenance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(maintenance)


class MaintenanceSelectionTest(unittest.TestCase):
    """What: メンテナンスが上限内の有効な未処理キャプチャだけを受け取る。"""

    def test_pending_metadata_is_filtered_and_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inbox = root / "runtime" / "inbox"
            inbox.mkdir(parents=True)
            for index in range(7):
                (inbox / f"{index}.json").write_text(
                    json.dumps({"status": "pending_distillation", "session_id": str(index)}),
                    encoding="utf-8",
                )
            (inbox / "processed.json").write_text(
                json.dumps({"status": "processed"}), encoding="utf-8"
            )
            (inbox / "invalid.json").write_text("not-json", encoding="utf-8")

            selected = maintenance.MaintenanceRunner(root, maintenance.MAX_SESSIONS_PER_RUN, None).pending_metadata()

            self.assertEqual(5, len(selected))
            self.assertTrue(all(path.name[0].isdigit() for path in selected))


if __name__ == "__main__":
    unittest.main()
