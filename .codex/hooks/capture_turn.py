from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path


MAX_TEXT_CHARS = 6000


def main() -> int:
    """How: journal bounded prompts/final messages so maintenance rarely needs raw transcripts."""
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        return 0
    if not isinstance(payload, dict):
        return 0
    aios_root = Path(__file__).resolve().parents[2]
    journal_dir = aios_root / "runtime" / "journal"
    session_id = sanitize(str(payload.get("session_id") or "unknown"))
    event = payload.get("hook_event_name")

    if event == "UserPromptSubmit":
        text = str(payload.get("prompt") or "")
        kind = "user_prompt"
    elif event == "Stop":
        text = str(payload.get("last_assistant_message") or "")
        kind = "assistant_final"
    else:
        return 0

    record = {
        "captured_at_unix": int(time.time()),
        "session_id": payload.get("session_id"),
        "turn_id": payload.get("turn_id"),
        "cwd": payload.get("cwd"),
        "model": payload.get("model"),
        "kind": kind,
        "text_chars": len(text),
        "text_sha256": hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest(),
        "text": bounded(text),
    }
    try:
        journal_dir.mkdir(parents=True, exist_ok=True)
        with (journal_dir / f"{session_id}.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"AIOS journal capture skipped: {exc}", file=sys.stderr)
    return 0


def bounded(text: str) -> str:
    """ジャーナルの上限を守りながら先頭と末尾の文脈を残す。"""
    if len(text) <= MAX_TEXT_CHARS:
        return text
    marker = "\n\n...[truncated for AIOS journal]...\n\n"
    available = max(0, MAX_TEXT_CHARS - len(marker))
    left = available // 2
    right = available - left
    return f"{text[:left]}{marker}{text[-right:]}"


def sanitize(value: str) -> str:
    """How: keep journal filenames portable."""
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value)[:96]


if __name__ == "__main__":
    raise SystemExit(main())
