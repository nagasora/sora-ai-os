from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path


BEGIN = "<!-- SORA-AIOS:BEGIN -->"
END = "<!-- SORA-AIOS:END -->"
ADDITIONAL_CONTEXT_LIMIT = 4000


class Installer:
    def __init__(self, repo_root: Path, home: Path) -> None:
        self.repo_root = repo_root.resolve()
        self.home = home.resolve()
        self.codex_home = self.home / ".codex"
        self.skills_home = self.home / ".agents" / "skills"

    def install(self) -> None:
        """How: install global routing, skills, and hooks while preserving unrelated user configuration."""
        self.codex_home.mkdir(parents=True, exist_ok=True)
        self.skills_home.mkdir(parents=True, exist_ok=True)
        self.install_agents()
        self.install_skills()
        self.install_hooks()
        print("Installed Sora AI Knowledge OS global routing, skills, and hooks.")
        print("Next: run Codex, open /hooks, review and trust the AIOS command hooks.")
        print("Optional: enable [features] memories = true in ~/.codex/config.toml.")

    def install_agents(self) -> None:
        target = self.codex_home / "AGENTS.md"
        policy = (self.repo_root / "global" / "AGENTS.md").read_text(encoding="utf-8").strip()
        block = f"{BEGIN}\n{policy}\n{END}"
        current = target.read_text(encoding="utf-8") if target.exists() else ""
        if BEGIN in current and END in current:
            before, rest = current.split(BEGIN, 1)
            _, after = rest.split(END, 1)
            updated = f"{before.rstrip()}\n\n{block}{after}"
        else:
            updated = f"{current.rstrip()}\n\n{block}\n" if current.strip() else f"{block}\n"
        target.write_text(updated, encoding="utf-8")

    def install_skills(self) -> None:
        source_root = self.repo_root / ".agents" / "skills"
        for source in sorted(path for path in source_root.iterdir() if path.is_dir()):
            target = self.skills_home / source.name
            if target.exists() or target.is_symlink():
                if target.is_symlink() and target.resolve() == source.resolve():
                    continue
                backup = next_backup_path(target)
                target.rename(backup)
            try:
                target.symlink_to(source, target_is_directory=True)
            except OSError:
                # Why not fail installation on Windows: symlink creation may require Developer Mode or elevated rights.
                shutil.copytree(source, target)

    def install_hooks(self) -> None:
        target = self.codex_home / "hooks.json"
        existing = {"description": "User hooks", "hooks": {}}
        if target.exists():
            try:
                existing = json.loads(target.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Cannot merge invalid {target}: {exc}") from exc
        if not isinstance(existing, dict):
            raise SystemExit(f"Cannot merge invalid {target}: root must be a JSON object")
        hooks = existing.setdefault("hooks", {})
        if not isinstance(hooks, dict):
            raise SystemExit(f"Cannot merge invalid {target}: hooks must be an object")
        python = Path(sys.executable).resolve()
        start_script = self.repo_root / ".codex" / "hooks" / "session_start.py"
        end_script = self.repo_root / ".codex" / "hooks" / "session_end.py"
        turn_script = self.repo_root / ".codex" / "hooks" / "capture_turn.py"
        start_cmd = quote_command(python, start_script)
        end_cmd = quote_command(python, end_script)
        turn_cmd = quote_command(python, turn_script)

        remove_aios_commands(hooks, str(start_script), str(end_script), str(turn_script))
        hooks.setdefault("SessionStart", []).append(
            {
                "matcher": "startup|resume|compact",
                "hooks": [
                    {
                        "type": "command",
                        "command": start_cmd,
                        "additionalContextLimit": ADDITIONAL_CONTEXT_LIMIT,
                        "statusMessage": "Loading AI Knowledge OS route",
                    }
                ],
            }
        )
        hooks.setdefault("UserPromptSubmit", []).append(
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": turn_cmd,
                        "timeout": 2,
                    }
                ]
            }
        )
        hooks.setdefault("Stop", []).append(
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": turn_cmd,
                        "timeout": 2,
                    }
                ]
            }
        )
        hooks.setdefault("SessionEnd", []).append(
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": end_cmd,
                        "timeout": 3,
                    }
                ]
            }
        )
        target.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def quote_command(python: Path, script: Path) -> str:
    """How: build one cross-platform command string with explicit executable/script paths."""
    return f'"{python}" "{script}"'


def next_backup_path(target: Path) -> Path:
    """既存バックアップを上書きしない退避先を返す。"""
    base = target.with_name(target.name + ".pre-aios-backup")
    candidate = base
    index = 1
    while candidate.exists() or candidate.is_symlink():
        candidate = target.with_name(f"{target.name}.pre-aios-backup-{index}")
        index += 1
    return candidate


def remove_aios_commands(hooks: dict[str, list], *needles: str) -> None:
    """同じグループの無関係なhandlerを残したままAIOS handlerだけを除去する。"""
    normalized_needles = tuple(needle.casefold() for needle in needles)
    for event in ("SessionStart", "UserPromptSubmit", "Stop", "SessionEnd"):
        groups = hooks.get(event, [])
        if not isinstance(groups, list):
            raise SystemExit(f"Cannot merge invalid hooks.{event}: expected a list")
        cleaned = []
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks", []), list):
                cleaned.append(group)
                continue
            handlers = group["hooks"]
            kept = []
            for handler in handlers:
                command = str(handler.get("command", "")) if isinstance(handler, dict) else ""
                if any(needle in command.casefold() for needle in normalized_needles):
                    continue
                kept.append(handler)
            if kept:
                updated_group = dict(group)
                updated_group["hooks"] = kept
                cleaned.append(updated_group)
            elif not handlers:
                cleaned.append(group)
        hooks[event] = cleaned


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install Sora AI Knowledge OS into local Codex")
    parser.add_argument("--home", type=Path, default=Path.home())
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    Installer(repo_root, args.home).install()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
