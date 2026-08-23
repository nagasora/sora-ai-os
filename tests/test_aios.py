from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "aios.py"
spec = importlib.util.spec_from_file_location("aios", MODULE_PATH)
aios = importlib.util.module_from_spec(spec)
assert spec.loader is not None
import sys
sys.modules["aios"] = aios
spec.loader.exec_module(aios)


class KnowledgeRepositoryTest(unittest.TestCase):
    """What: deterministic indexing, retrieval, and metadata validation keep knowledge routing reliable."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for folder in aios.KNOWLEDGE_DIRS:
            (self.root / "knowledge" / folder).mkdir(parents=True, exist_ok=True)
        (self.root / "scripts").mkdir(parents=True, exist_ok=True)
        (self.root / "scripts" / "aios.py").write_text("# placeholder", encoding="utf-8")
        self.repo = aios.KnowledgeRepository(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_add_candidate_can_be_searched(self) -> None:
        path = self.repo.add_candidate(
            title="Group-aware validation prevents leakage",
            summary="Use group-disjoint folds when entities repeat across rows.",
            domain="kaggle",
            tags="cv, leakage, groupkfold",
            evidence="project://example",
        )
        self.assertTrue(path.exists())
        results = self.repo.search("group leakage", limit=3)
        self.assertEqual("candidate", results[0]["type"])
        self.assertIn("leakage", results[0]["title"].lower())

    def test_validate_rejects_missing_fields(self) -> None:
        bad = self.root / "knowledge" / "patterns" / "P-0001-bad.md"
        bad.write_text("---\nid: P-0001\ntype: pattern\n---\nBody\n", encoding="utf-8")
        errors = self.repo.validate()
        self.assertTrue(any("missing fields" in error for error in errors))

    def test_make_fts_query_sanitizes_syntax(self) -> None:
        query = aios.make_fts_query('foo OR "bar:baz"')
        self.assertNotIn(":", query)
        self.assertIn('"foo"', query)

    def test_search_falls_back_for_japanese_and_refreshes_index(self) -> None:
        self.repo.search("not-present", limit=3)
        entry = self.root / "knowledge" / "patterns" / "P-0001-japanese-search.md"
        entry.write_text(
            aios.render_entry(
                {
                    "id": "P-0001",
                    "type": "pattern",
                    "title": "日本語の知識検索",
                    "summary": "SQLite FTS5だけに頼らず部分一致を補完する。",
                    "domain": "ai-agent-operations",
                    "status": "active",
                    "confidence": "medium",
                    "observed_count": "1",
                    "created": "2026-08-23",
                    "last_verified": "2026-08-23",
                    "tags": "日本語,検索",
                    "evidence": "project://test",
                },
                "## Pattern\n\n日本語の検索結果を返す。",
            ),
            encoding="utf-8",
        )
        results = self.repo.search("知識検索", limit=3)
        self.assertEqual("P-0001", results[0]["id"])

    def test_search_respects_non_positive_limit(self) -> None:
        self.assertEqual([], self.repo.search("anything", limit=0))


if __name__ == "__main__":
    unittest.main()
