from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


KNOWLEDGE_DIRS = ("candidates", "patterns", "decisions", "failures", "playbooks")
REQUIRED_FIELDS = {
    "id",
    "type",
    "title",
    "summary",
    "domain",
    "status",
    "confidence",
    "observed_count",
    "created",
    "last_verified",
    "tags",
    "evidence",
}
TYPE_PRIORITY = {
    "playbook": 5,
    "pattern": 4,
    "decision": 3,
    "failure": 3,
    "candidate": 1,
}
STOP_WORDS = {"and", "or", "not"}


@dataclass(frozen=True)
class Entry:
    path: Path
    metadata: dict[str, str]
    body: str

    @property
    def entry_id(self) -> str:
        return self.metadata.get("id", self.path.stem)


class KnowledgeRepository:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.knowledge_root = root / "knowledge"
        self.state_root = root / ".aios"
        self.db_path = self.state_root / "index.sqlite3"

    def iter_entries(self) -> Iterable[Entry]:
        for folder in KNOWLEDGE_DIRS:
            base = self.knowledge_root / folder
            if not base.exists():
                continue
            for path in sorted(base.rglob("*.md")):
                if path.name.startswith("."):
                    continue
                yield parse_entry(path)

    def rebuild_index(self) -> int:
        self.state_root.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        try:
            connection.execute("DROP TABLE IF EXISTS entries_fts")
            connection.execute("DROP TABLE IF EXISTS entries")
            connection.execute("DROP TABLE IF EXISTS index_metadata")
            connection.execute(
                "CREATE TABLE entries (id TEXT PRIMARY KEY, type TEXT, title TEXT, summary TEXT, "
                "domain TEXT, status TEXT, confidence TEXT, observed_count INTEGER, tags TEXT, "
                "last_verified TEXT, path TEXT, body TEXT)"
            )
            connection.execute(
                "CREATE VIRTUAL TABLE entries_fts USING fts5(id, title, summary, domain, tags, body, content='entries', content_rowid='rowid')"
            )
            connection.execute(
                "CREATE TABLE index_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            count = 0
            for entry in self.iter_entries():
                meta = entry.metadata
                connection.execute(
                    "INSERT INTO entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        entry.entry_id,
                        meta.get("type", ""),
                        meta.get("title", ""),
                        meta.get("summary", ""),
                        meta.get("domain", ""),
                        meta.get("status", ""),
                        meta.get("confidence", ""),
                        to_int(meta.get("observed_count", "0")),
                        meta.get("tags", ""),
                        meta.get("last_verified", ""),
                        str(entry.path.relative_to(self.root)),
                        entry.body,
                    ),
                )
                count += 1
            connection.execute(
                "INSERT INTO entries_fts(rowid, id, title, summary, domain, tags, body) "
                "SELECT rowid, id, title, summary, domain, tags, body FROM entries"
            )
            connection.execute(
                "INSERT INTO index_metadata(key, value) VALUES (?, ?)",
                ("knowledge_fingerprint", self.knowledge_fingerprint()),
            )
            connection.commit()
            return count
        finally:
            connection.close()

    def search(self, query: str, limit: int) -> list[dict[str, object]]:
        if limit <= 0:
            return []
        if not self.db_path.exists() or not self.index_is_current():
            self.rebuild_index()
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            fts_query = make_fts_query(query)
            if fts_query:
                rows = connection.execute(
                    "SELECT e.*, bm25(entries_fts, 8.0, 5.0, 4.0, 2.0, 2.0, 1.0) AS rank "
                    "FROM entries_fts JOIN entries e ON e.rowid = entries_fts.rowid "
                    "WHERE entries_fts MATCH ? LIMIT ?",
                    (fts_query, max(limit * 4, limit)),
                ).fetchall()
            else:
                rows = []
            scored: list[dict[str, object]] = []
            for row in rows:
                item = dict(row)
                priority = TYPE_PRIORITY.get(str(item.get("type")), 0)
                confidence_bonus = {"high": 2, "medium": 1, "low": 0}.get(str(item.get("confidence")), 0)
                status_penalty = 5 if item.get("status") in {"stale", "archived", "superseded"} else 0
                item["score"] = -float(item["rank"]) + priority + confidence_bonus - status_penalty
                scored.append(item)

            # SQLiteの標準tokenizerは日本語を安定して分割しないため、
            # 通常の検索はFTS5を使い、限定的な部分一致で補完する。

            seen_ids = {str(item["id"]) for item in scored}
            scored.extend(self.fallback_search(query, seen_ids))
            scored.sort(key=lambda x: float(x["score"]), reverse=True)
            return scored[:limit]
        finally:
            connection.close()

    def index_is_current(self) -> bool:
        """SQLiteインデックスが現在の知識ファイルを反映しているか返す。"""
        try:
            connection = sqlite3.connect(self.db_path)
            try:
                row = connection.execute(
                    "SELECT value FROM index_metadata WHERE key = ?",
                    ("knowledge_fingerprint",),
                ).fetchone()
            finally:
                connection.close()
        except sqlite3.Error:
            return False
        return bool(row and row[0] == self.knowledge_fingerprint())

    def knowledge_fingerprint(self) -> str:
        """追跡対象の知識ファイルから変更検知用の識別値を作る。"""
        digest = hashlib.sha256()
        for entry in self.iter_entries():
            stat = entry.path.stat()
            relative = entry.path.relative_to(self.root).as_posix()
            digest.update(f"{relative}\0{stat.st_mtime_ns}\0{stat.st_size}\n".encode("utf-8"))
        return digest.hexdigest()

    def fallback_search(self, query: str, exclude_ids: set[str]) -> list[dict[str, object]]:
        """tokenizerで扱えない検索を正規化済み部分一致で補完する。"""
        terms = search_terms(query)
        if not terms:
            return []
        phrase = normalize_search_text(query).strip()
        matches: list[dict[str, object]] = []
        for entry in self.iter_entries():
            if entry.entry_id in exclude_ids:
                continue
            meta = entry.metadata
            title = normalize_search_text(meta.get("title", ""))
            summary = normalize_search_text(meta.get("summary", ""))
            tags = normalize_search_text(meta.get("tags", ""))
            domain = normalize_search_text(meta.get("domain", ""))
            body = normalize_search_text(entry.body)
            searchable = " ".join((title, summary, domain, tags, body))
            matched = [term for term in terms if term in searchable]
            if not matched:
                continue
            priority = TYPE_PRIORITY.get(meta.get("type", ""), 0)
            confidence_bonus = {"high": 2, "medium": 1, "low": 0}.get(meta.get("confidence", ""), 0)
            status_penalty = 5 if meta.get("status") in {"stale", "archived", "superseded"} else 0
            score = (
                len(matched)
                + (2 * sum(term in title for term in matched))
                + sum(term in summary for term in matched)
                + (1.5 if phrase and phrase in searchable else 0)
                + priority
                + confidence_bonus
                - status_penalty
            )
            matches.append(
                {
                    "id": entry.entry_id,
                    "type": meta.get("type", ""),
                    "title": meta.get("title", ""),
                    "summary": meta.get("summary", ""),
                    "domain": meta.get("domain", ""),
                    "status": meta.get("status", ""),
                    "confidence": meta.get("confidence", ""),
                    "observed_count": to_int(meta.get("observed_count", "0")),
                    "tags": meta.get("tags", ""),
                    "last_verified": meta.get("last_verified", ""),
                    "path": str(entry.path.relative_to(self.root)),
                    "score": score,
                }
            )
        return matches

    def validate(self) -> list[str]:
        errors: list[str] = []
        seen: dict[str, Path] = {}
        for entry in self.iter_entries():
            missing = sorted(REQUIRED_FIELDS - set(entry.metadata))
            if missing:
                errors.append(f"{entry.path}: missing fields: {', '.join(missing)}")
            entry_id = entry.entry_id
            if entry_id in seen:
                errors.append(f"duplicate id {entry_id}: {seen[entry_id]} and {entry.path}")
            seen[entry_id] = entry.path
            declared_type = entry.metadata.get("type")
            expected_type = singularize(entry.path.parent.name)
            if declared_type and declared_type != expected_type:
                errors.append(f"{entry.path}: type={declared_type!r} does not match folder {expected_type!r}")
        return errors

    def add_candidate(self, title: str, summary: str, domain: str, tags: str, evidence: str) -> Path:
        today = date.today().isoformat()
        slug = slugify(title)
        seq = next_sequence(self.knowledge_root / "candidates", prefix="C")
        entry_id = f"C-{seq:04d}"
        path = self.knowledge_root / "candidates" / f"{entry_id}-{slug}.md"
        content = render_entry(
            {
                "id": entry_id,
                "type": "candidate",
                "title": title,
                "summary": summary,
                "domain": domain,
                "status": "active",
                "confidence": "low",
                "observed_count": "1",
                "created": today,
                "last_verified": today,
                "tags": tags,
                "evidence": evidence,
            },
            body=(
                "## Observation\n\n"
                f"{summary}\n\n"
                "## Reuse condition\n\n"
                "Describe when this observation should change a future decision.\n\n"
                "## Counterevidence / limits\n\n"
                "Record cases where this may not apply.\n"
            ),
        )
        path.write_text(content, encoding="utf-8")
        self.rebuild_index()
        return path


def parse_entry(path: Path) -> Entry:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return Entry(path, {}, text)
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return Entry(path, {}, text)
    metadata: dict[str, str] = {}
    for raw_line in parts[1].splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return Entry(path, metadata, parts[2].lstrip())


def render_entry(metadata: dict[str, str], body: str) -> str:
    ordered = [
        "id",
        "type",
        "title",
        "summary",
        "domain",
        "status",
        "confidence",
        "observed_count",
        "created",
        "last_verified",
        "tags",
        "evidence",
    ]
    lines = ["---"]
    for key in ordered:
        value = metadata[key].replace("\n", " ").strip()
        lines.append(f'{key}: "{value.replace(chr(34), chr(39))}"')
    lines.extend(["---", "", body.rstrip(), ""])
    return "\n".join(lines)


def make_fts_query(query: str) -> str:
    tokens = search_terms(query)
    # Why not use raw user text in MATCH: SQLite FTS syntax characters can cause query errors.
    return " OR ".join(f'"{token.replace(chr(34), "")}"' for token in tokens[:12])


def search_terms(query: str) -> list[str]:
    """FTS5と日本語部分一致の両方で使う検索語を正規化する。"""
    terms: list[str] = []
    for raw in re.findall(r"[\w\-]+", query, flags=re.UNICODE):
        term = normalize_search_text(raw)
        if len(term) > 1 and term not in STOP_WORDS and term not in terms:
            terms.append(term)
    return terms[:12]


def normalize_search_text(value: str) -> str:
    """全角・半角と大文字・小文字を正規化して照合する。"""
    return unicodedata.normalize("NFKC", value).casefold()


def slugify(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9ぁ-んァ-ヶ一-龯]+", "-", value).strip("-").lower()
    return normalized[:64] or "entry"


def to_int(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        return 0


def singularize(folder: str) -> str:
    return {
        "candidates": "candidate",
        "patterns": "pattern",
        "decisions": "decision",
        "failures": "failure",
        "playbooks": "playbook",
    }.get(folder, folder)


def next_sequence(folder: Path, prefix: str) -> int:
    highest = 0
    if folder.exists():
        pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)")
        for path in folder.glob(f"{prefix}-*.md"):
            match = pattern.match(path.name)
            if match:
                highest = max(highest, int(match.group(1)))
    return highest + 1


def find_root(start: Path) -> Path:
    for path in (start.resolve(), *start.resolve().parents):
        if (path / "knowledge").exists() and (path / "scripts" / "aios.py").exists():
            return path
    raise SystemExit("Could not find AI Knowledge OS root.")


def cmd_search(repo: KnowledgeRepository, args: argparse.Namespace) -> int:
    results = repo.search(args.query, args.limit)
    for item in results:
        print(
            json.dumps(
                {
                    "id": item["id"],
                    "type": item["type"],
                    "title": item["title"],
                    "summary": item["summary"],
                    "status": item["status"],
                    "confidence": item["confidence"],
                    "observed_count": item["observed_count"],
                    "last_verified": item["last_verified"],
                    "path": item["path"],
                    "score": round(float(item["score"]), 3),
                },
                ensure_ascii=False,
            )
        )
    return 0


def cmd_show(repo: KnowledgeRepository, args: argparse.Namespace) -> int:
    for entry in repo.iter_entries():
        if entry.entry_id == args.entry_id:
            print(entry.path.read_text(encoding="utf-8"))
            return 0
    print(f"Entry not found: {args.entry_id}", file=sys.stderr)
    return 1


def cmd_validate(repo: KnowledgeRepository, _: argparse.Namespace) -> int:
    errors = repo.validate()
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    count = repo.rebuild_index()
    print(f"OK: {count} knowledge entries validated and indexed.")
    return 0


def cmd_index(repo: KnowledgeRepository, _: argparse.Namespace) -> int:
    count = repo.rebuild_index()
    print(f"Indexed {count} entries -> {repo.db_path}")
    return 0


def cmd_add_candidate(repo: KnowledgeRepository, args: argparse.Namespace) -> int:
    path = repo.add_candidate(args.title, args.summary, args.domain, args.tags, args.evidence)
    print(path.relative_to(repo.root))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Knowledge OS deterministic CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    search = sub.add_parser("search", help="Search curated knowledge")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=3)

    show = sub.add_parser("show", help="Show one entry by id")
    show.add_argument("entry_id")

    sub.add_parser("validate", help="Validate metadata and rebuild index")
    sub.add_parser("index", help="Rebuild search index")

    add = sub.add_parser("add-candidate", help="Add a first-observation candidate")
    add.add_argument("--title", required=True)
    add.add_argument("--summary", required=True)
    add.add_argument("--domain", required=True)
    add.add_argument("--tags", default="")
    add.add_argument("--evidence", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    """How: expose a small deterministic interface so Codex retrieves less text and does less repeated reasoning."""
    parser = build_parser()
    args = parser.parse_args(argv)
    default_root = Path(__file__).resolve().parents[1]
    root = Path(os.environ.get("AIOS_HOME", str(default_root))).expanduser().resolve()
    repo = KnowledgeRepository(root)
    handlers = {
        "search": cmd_search,
        "show": cmd_show,
        "validate": cmd_validate,
        "index": cmd_index,
        "add-candidate": cmd_add_candidate,
    }
    return handlers[args.command](repo, args)


if __name__ == "__main__":
    raise SystemExit(main())
