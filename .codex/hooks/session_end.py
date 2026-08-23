from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path


def main() -> int:
    """How: spool every Codex main-session capture into the central AIOS inbox within the SessionEnd time ceiling."""
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        return 0
    if not isinstance(payload, dict):
        return 0
    aios_root = Path(__file__).resolve().parents[2]
    inbox = aios_root / "runtime" / "inbox"
    try:
        inbox.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"AIOS session capture skipped: {exc}", file=sys.stderr)
        return 0
    session_id = sanitize(str(payload.get("session_id") or f"session-{int(time.time())}"))
    stamp = int(time.time())

    capture = {
        "session_id": payload.get("session_id"),
        "captured_at_unix": stamp,
        "cwd": payload.get("cwd"),
        "model": payload.get("model"),
        "reason": payload.get("reason"),
        "transcript_copy": None,
        "status": "pending_distillation",
    }

    transcript = payload.get("transcript_path")
    if transcript:
        source = Path(str(transcript))
        if source.exists() and source.is_file():
            target = unique_path(inbox / f"{stamp}-{session_id}.transcript.jsonl")
            try:
                # Why not parse here: Codex documents transcript format as unstable and SessionEnd supports only a short timeout.
                shutil.copyfile(source, target)
                capture["transcript_copy"] = str(target)
            except OSError as exc:
                capture["transcript_error"] = str(exc)

    meta = unique_path(inbox / f"{stamp}-{session_id}.json")
    try:
        meta.write_text(json.dumps(capture, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        print(f"AIOS session metadata capture skipped: {exc}", file=sys.stderr)
    return 0


def unique_path(path: Path) -> Path:
    """同一秒のhook再試行でキャプチャを上書きしない。"""
    candidate = path
    index = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        index += 1
    return candidate


def sanitize(value: str) -> str:
    """How: keep capture filenames portable across Windows/macOS/Linux."""
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value)[:96]


if __name__ == "__main__":
    raise SystemExit(main())
