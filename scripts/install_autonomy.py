"""Install the shared execution contract without changing tool permissions."""
from __future__ import annotations

import argparse
import difflib
import shutil
from pathlib import Path

BEGIN = '<!-- SORA-AUTONOMY:BEGIN -->'
END = '<!-- SORA-AUTONOMY:END -->'
ROOT = Path(__file__).resolve().parents[1]


def merge(current: str, policy: str) -> str:
    block = f'{BEGIN}\n{policy.strip()}\n{END}'
    if BEGIN in current or END in current:
        if current.count(BEGIN) != 1 or current.count(END) != 1:
            raise ValueError('Invalid autonomy markers; refusing to overwrite')
        before, rest = current.split(BEGIN)
        if END not in rest:
            raise ValueError('Reversed autonomy markers')
        _, after = rest.split(END)
        return before + block + after
    return current.rstrip() + ('\n\n' if current.strip() else '') + block + '\n'


def install(home: Path, apply: bool) -> int:
    policy = (ROOT / 'global/AUTONOMOUS.md').read_text()
    plan = []
    for relative in ('.codex/AGENTS.md', '.claude/CLAUDE.md'):
        target = home / relative
        current = target.read_text() if target.exists() else ''
        updated = merge(current, policy)
        plan.append((target, current, updated))
    changed = 0
    for target, current, updated in plan:
        if current == updated:
            continue
        changed += 1
        print(''.join(difflib.unified_diff(current.splitlines(True), updated.splitlines(True), fromfile=str(target), tofile=str(target))), end='')
        if apply:
            if target.exists():
                backup = target.with_name(target.name + '.pre-autonomy-backup')
                index = 1
                while backup.exists():
                    backup = target.with_name(target.name + f'.pre-autonomy-backup-{index}')
                    index += 1
                shutil.copy2(target, backup)
                print(f'Backup: {backup}')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(updated)
            if target.read_text() != updated:
                raise OSError(f'Verification failed: {target}')
    print(f'{"Applied" if apply else "Preview"}: {changed} changed files')
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--apply', action='store_true', help='Write settings; default is preview only')
    args = parser.parse_args()
    install(args.home.expanduser().resolve(), args.apply)


if __name__ == '__main__':
    main()
