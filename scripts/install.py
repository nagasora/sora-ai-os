from __future__ import annotations

import argparse
import copy
import hashlib
import re
import tomllib
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


AGENT_BEGIN = "<!-- SORA-AGENT-TREE:BEGIN -->"
AGENT_END = "<!-- SORA-AGENT-TREE:END -->"


def merge_toml_settings(content: str, section: str, settings: dict[str, object]) -> str:
    """対象テーブルの指定キーだけを更新し、無関係な設定とコメントを保持する。"""
    expected = copy.deepcopy(tomllib.loads(content))
    expected_target = expected.setdefault(section, {}) if section else expected
    expected_target.update(settings)
    headers = list(re.finditer(r"(?m)^\s*\[[^\n]+\][ \t]*(?:#[^\n]*)?$", content))
    start, end = 0, headers[0].start() if headers else len(content)
    if section:
        matches = [header for header in headers if header.group().strip().split("#", 1)[0].strip() == f"[{section}]"]
        if not matches:
            content = content.rstrip() + f"\n\n[{section}]\n"
            start = end = len(content)
        else:
            header = matches[0]
            start = header.end()
            end = next((item.start() for item in headers if item.start() > header.start()), len(content))
    block = content[start:end]
    for key, value in settings.items():
        pattern = rf"(?m)^[ \t]*{re.escape(key)}[ \t]*=[^\n]*"
        line = f"{key} = {json.dumps(value, ensure_ascii=False)}"
        if re.search(pattern, block):
            block = re.sub(pattern, lambda _: line, block)
        else:
            block = block.rstrip() + "\n" + line + "\n"
    updated = content[:start] + block + content[end:]
    parsed = tomllib.loads(updated)
    target = parsed[section] if section else parsed
    if parsed != expected or any(target.get(key) != value for key, value in settings.items()):
        raise ValueError(f"Cannot safely update TOML section {section!r}")
    return updated


def merge_agent_policy(content: str, policy: str) -> str:
    """旧単独エージェント節を置換し、プロジェクト固有の他の指示を保持する。"""
    content = re.sub(
        r"(?ms)^## Single-agent policy\r?\n.*?(?=^#{1,2} |\Z)", "", content
    )
    replacements = {
        "12. Subagent Policy": "Use the cost-efficient agent tree below. Delegate bounded work on demand.",
        "13. Single-agent Task Contract": "Root owns scope and acceptance criteria, integrates and verifies delegated work. Self-review is not independent review.",
    }
    for heading, text in replacements.items():
        content = re.sub(
            rf"(?ms)^# {re.escape(heading)}\r?\n.*?(?=^# |\Z)",
            f"# {heading.replace('Single-agent', 'Agent')}\n\n{text}\n\n---\n\n",
            content,
        )
    content = content.replace(
        "- Do not use Codex subagents. The current primary agent handles all work itself.",
        "- Delegate only bounded useful work under the cost-efficient agent tree.",
    )
    migrations = {
        "本プロジェクトでは、メインのプロジェクトマネージャー、独立した実装担当、独立したレビュー担当の3つの運用役を採用します。": "本プロジェクトでは、Astra mediumが統括し、必要に応じてLuna maxの調査役とSol highの実装役へ委譲します。Astra xhighの独立レビューは具体的なリスクがある場合だけ実施します。",
        "### 2. ⚙️ 実装担当 (Implementer)": "### 2. ⚙️ 実装担当 (Worker / Sol high)",
        "2. **PM**: 所有ファイルと受入条件を定めたTask Packetを作り、`implementer`へ委譲する。": "2. **PM**: 分担が有益な場合だけ、所有ファイルと受入条件を定めたTask Packetを作り、`worker`へ委譲する。小さな作業は統括が実施する。",
        "3. **Implementer**:": "3. **Worker**:",
        "4. **Reviewer**: 実装担当から独立して成果物を確認し、必要に応じて修正要請を返す。": "4. **PM / Reviewer**: PMが統合・検証する。具体的なリスクまたは明示依頼がある場合だけ、Astra xhighの`reviewer`が独立に確認する。",
        "- Jobs performs the work and verification itself and reports evidence, decisions, progress, risks, and approval requests to the Owner.": "- Jobs uses Astra medium, delegates bounded work on demand, integrates and verifies results, and reports evidence, decisions, progress, risks, and approval requests to the Owner.",
        "6. Use only the current primary agent for all work.": "6. Use the cost-efficient agent tree below; delegate only useful bounded work.",
        "12. Jobs performs implementation and verification sequentially without subagents.": "12. Jobs integrates and verifies results; independent Astra xhigh review is optional and risk-driven."
    }
    for old, updated in migrations.items():
        content = content.replace(old, updated)
    if not policy:
        return content
    block = f"{AGENT_BEGIN}\n{policy.strip()}\n{AGENT_END}"
    if AGENT_BEGIN in content or AGENT_END in content:
        if content.count(AGENT_BEGIN) != 1 or content.count(AGENT_END) != 1:
            raise ValueError("Invalid agent policy markers")
        before, rest = content.split(AGENT_BEGIN, 1)
        _, after = rest.split(AGENT_END, 1)
        return before + block + after
    return content.rstrip() + "\n\n" + block + "\n"


def plan_agent_tree(repo_root: Path, home: Path, projects: list[Path]) -> dict[Path, str | None]:
    """個人設定と明示されたプロジェクトだけの更新内容を、書き込み前に構築する。"""
    policy = (repo_root / "global" / "AGENTS.md").read_text(encoding="utf-8")
    tree = policy.split("## Cost-efficient agent tree", 1)[1].split("\n## ", 1)[0]
    tree = "## Cost-efficient agent tree" + tree
    roles = {}
    for source in sorted((repo_root / "global" / "agents").glob("*.toml")):
        text = source.read_text(encoding="utf-8")
        role = tomllib.loads(text)
        roles[role["name"]] = text
    if set(roles) != {"explorer", "worker", "researcher", "reviewer"}:
        raise ValueError("Expected exactly four agent roles")
    codex_home = home.resolve() / ".codex"
    plan: dict[Path, str | None] = {}
    roots = list(dict.fromkeys(path.resolve() for path in projects))
    for root in roots:
        if not root.is_dir():
            raise ValueError(f"Project directory does not exist: {root}")
    for config_dir in [codex_home] + [root / ".codex" for root in roots]:
        target = config_dir / "config.toml"
        content = target.read_text(encoding="utf-8-sig") if target.exists() else ""
        content = merge_toml_settings(content, "", {
            "model": "gpt-6-astra", "model_reasoning_effort": "medium",
        })
        content = content.replace("# User policy: run only the primary agent.\n", "")
        content = merge_toml_settings(content, "features", {"multi_agent": True})
        content = merge_toml_settings(content, "agents", {
            "enabled": True, "max_concurrent_threads_per_session": 3,
        })
        plan[target] = content
        # 個人の役割を継承するため、各プロジェクトには重複した役割ファイルを新設しない。
        for existing in (config_dir / "agents").glob("*.toml"):
            role = tomllib.loads(existing.read_text(encoding="utf-8-sig"))
            if existing.name == "config.toml" and "name" not in role and role == {"features": {"multi_agent": False}}:
                plan[existing] = None
            elif role.get("name", existing.stem) in roles:
                plan[existing] = roles[role.get("name", existing.stem)]
    for name, text in roles.items():
        plan[codex_home / "agents" / f"{name}.toml"] = text
    for target in [codex_home / "AGENTS.md"] + [root / "AGENTS.md" for root in roots]:
        content = target.read_text(encoding="utf-8-sig") if target.exists() else ""
        if target == repo_root.resolve() / "AGENTS.md":
            continue
        if target == codex_home / "AGENTS.md" and BEGIN in content and END in content:
            before, rest = content.split(BEGIN, 1)
            _, after = rest.split(END, 1)
            content = before + BEGIN + "\n" + policy.strip() + "\n" + END + after
        plan[target] = merge_agent_policy(content, "" if target == codex_home / "AGENTS.md" and BEGIN in content else tree)
    return plan


def install_agent_tree(repo_root: Path, home: Path, projects: list[Path], dry_run: bool) -> None:
    """更新一覧を表示し、適用時は変更前のファイルをruntimeへ退避する。"""
    plan = plan_agent_tree(repo_root, home, projects)
    changed = 0
    for target, content in plan.items():
        current = target.read_text(encoding="utf-8-sig") if target.exists() else None
        if current == content:
            continue
        print(f"{'PLAN' if dry_run else 'WRITE'} {target}")
        changed += 1
        if dry_run:
            continue
        if target.exists():
            digest = hashlib.sha256(str(target).encode("utf-8")).hexdigest()[:12]
            backup = repo_root / "runtime" / "agent-tree-backups" / f"{target.name}-{digest}"
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, next_backup_path(backup) if backup.exists() else backup)
        if content is None:
            target.unlink()
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
    print(f"Agent tree: {changed} changed files; {len(projects)} requested projects.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install Sora AI Knowledge OS into local Codex")
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--agent-tree-only", action="store_true", help="Install only agent policy and model settings")
    parser.add_argument("--project", type=Path, action="append", default=[])
    parser.add_argument("--dry-run", action="store_true", help="Preview agent tree changes without writes")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    if args.agent_tree_only:
        install_agent_tree(repo_root, args.home, args.project, args.dry_run)
    elif args.project or args.dry_run:
        raise SystemExit("--project and --dry-run require --agent-tree-only")
    else:
        Installer(repo_root, args.home).install()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
