from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    """How: inject a bounded global retrieval route without loading the knowledge corpus."""
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        return 0
    if not isinstance(payload, dict):
        return 0
    aios_root = Path(__file__).resolve().parents[2]
    inbox = aios_root / "runtime" / "inbox"
    pending = len(list(inbox.glob("*.json"))) if inbox.exists() else 0
    search_cmd = f'python "{aios_root / "scripts" / "aios.py"}" search'
    context = (
        f"AI Knowledge OS home: {aios_root}. "
        f"Before broad external research, search curated knowledge with: {search_cmd} \"<query>\" --limit 3. "
        f"Pending local session captures: {pending}. Do not load raw captures into context unless running knowledge maintenance."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": context,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
