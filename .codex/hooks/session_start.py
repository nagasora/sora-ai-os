from __future__ import annotations

import json
import sys
from pathlib import Path


SIMPLE_ENGINEERING_GUIDANCE = """# Simple Engineering

## Keep it simple and elegant

Overengineering is a shameful and foolish act, and it is important to always pursue simple and elegant solutions.

Before implementing a feature or fixing a bug, consider all options. Instead of just listing similar choices or being bound by preconceptions and previous thinking, consider all options, including completely different approaches. Among the available options, choose the one that is the clearest, simplest, requires the fewest lines of code, and meets the user's requirements. There is no need to use iron plates and nails to repair torn clothes. Choose a right-sized, simple approach rather than an overly large and complex one.

Also avoid bringing unnecessary complexity into your code. Carefully examine related processing to ensure there are no impossible conditional branches or unnecessary try-catch blocks. Check the type definitions and actual processing, and remove any impossible conditional branches. There is no need to wrap code in a new try-catch block if an exception is unlikely to occur normally or if a try-catch already exists inside the called function.

## Avoid reinventing the wheel

Reinventing the wheel should be avoided. Before adding code, check whether existing code in the project or the project's dependencies already provide functionality that covers part or all of that processing. When implementing complex processing, investigate whether a popular and well-maintained library that achieves equivalent functionality exists, and if so, propose using it to the user.

## Keep only necessary changes

Keep the YAGNI (You aren't gonna need it) principle in mind. You should not introduce complexity just because you might need it in the future. Also, there is no need to maintain backward compatibility for unreleased features.

The code ultimately delivered to the user should be such that every line of change is necessary and no unnecessary code remains. Carefully review the diff line by line, rather than file by file, to ensure that all changes are truly necessary.

## Establish a shared understanding

If 'request_user_input tool is available, actively use it when asking the user questions, especially while running the grilling session. Do not use it for a single yes/no question; instead, use it when asking multiple questions at once or when presenting multiple options. The tool description specifies limiting the number of questions to between one and three, but this is merely a recommendation rather than a functional constraint. Use the 'request_user_input tool even if there are four or more questions.
"""


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
    context = build_context(aios_root, pending)
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


def build_context(aios_root: Path, pending: int) -> str:
    """セッション開始時に全プロジェクトへ注入する共通コンテキストを組み立てる。"""
    search_cmd = f'python "{aios_root / "scripts" / "aios.py"}" search'
    route = (
        f"AI Knowledge OS home: {aios_root}. "
        f"Before broad external research, search curated knowledge with: {search_cmd} \"<query>\" --limit 3. "
        f"Pending local session captures: {pending}. Do not load raw captures into context unless running knowledge maintenance."
    )
    harness = """# Implementation Harness

For code changes, fix the smallest complete slice and state scope/done/out-of-scope briefly. Reuse the nearest existing implementation and test. Default test budget: one reusable test unit per feature; extend or parameterize an existing test before creating a file. Add tests for observable behavior, regressions, or material risk only.

Run one focused test command first and stop when it passes unless the change crosses module/API/schema/concurrency/security/build boundaries, CI requires broader validation, or the user asks. For GitHub-backed changes, completion requires a scoped diff, proportionate validation, and an opened pull request with its URL; otherwise report BLOCKED rather than claiming completion.
"""
    return f"{route}\n\n{SIMPLE_ENGINEERING_GUIDANCE}\n\n{harness}"


if __name__ == "__main__":
    raise SystemExit(main())
