from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


class MeteredCodex:
    def __init__(self, aios_root: Path, workdir: Path) -> None:
        self.aios_root = aios_root
        self.workdir = workdir

    def run(self, args: argparse.Namespace) -> int:
        """How: run a normal Codex task while recording only aggregate usage for repeatable A/B comparisons."""
        if shutil.which("codex") is None:
            print("Codex CLI was not found on PATH.", file=sys.stderr)
            return 2
        command = ["codex", "exec", "--ephemeral", "--json", "--sandbox", args.sandbox]
        if args.baseline:
            command.append("--ignore-user-config")
        if args.model:
            command.extend(["--model", args.model])
        command.append(args.prompt)

        usage: dict[str, int] | None = None
        final_message = ""
        started = int(time.time())
        process = subprocess.Popen(
            command,
            cwd=self.workdir,
            stdout=subprocess.PIPE,
            stderr=None,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert process.stdout is not None
        for line in process.stdout:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "turn.completed":
                usage = event.get("usage")
            item = event.get("item") or {}
            if event.get("type") == "item.completed" and item.get("type") == "agent_message":
                final_message = item.get("text") or final_message
        code = process.wait()
        self.record(args, started, code, usage)
        if final_message:
            print(final_message)
        return code

    def record(self, args: argparse.Namespace, started: int, code: int, usage: dict[str, int] | None) -> None:
        """How: store aggregate counts and experiment labels without persisting prompt contents."""
        metrics = self.aios_root / "metrics"
        metrics.mkdir(exist_ok=True)
        usage = usage or {}
        input_tokens = int(usage.get("input_tokens", 0) or 0)
        cached = int(usage.get("cached_input_tokens", 0) or 0)
        record = {
            "started_at_unix": started,
            "label": args.label,
            "mode": "baseline" if args.baseline else "aios",
            "cwd": str(self.workdir),
            "model": args.model,
            "exit_code": code,
            "usage": usage,
            "cached_input_ratio": (cached / input_tokens) if input_tokens else None,
        }
        with (metrics / "task-usage.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a metered Codex exec task")
    parser.add_argument("prompt")
    parser.add_argument("--label", default="unlabeled")
    parser.add_argument("--baseline", action="store_true", help="Ignore user config to approximate a no-AIOS baseline")
    parser.add_argument("--model", default=None)
    parser.add_argument("--sandbox", default="workspace-write", choices=("read-only", "workspace-write", "danger-full-access"))
    parser.add_argument("--workdir", type=Path, default=Path.cwd())
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    aios_root = Path(__file__).resolve().parents[1]
    return MeteredCodex(aios_root, args.workdir.resolve()).run(args)


if __name__ == "__main__":
    raise SystemExit(main())
