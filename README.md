# Sora AI Knowledge OS

A lightweight Git-backed knowledge layer for Codex that aims to make future work start from prior verified decisions instead of repeating research.

## Architecture

- `global/AGENTS.md`: tiny always-on router/policy.
- `.agents/skills/`: reusable workflows loaded progressively by Codex.
- `knowledge/`: curated Git-tracked knowledge.
- `scripts/aios.py`: deterministic local search/index/validation CLI.
- `.codex/hooks/`: global capture scripts installed into the user-level Codex hook configuration.
- `runtime/inbox/` + `runtime/journal/`: raw/bounded local captures; never Git-tracked.
- `scripts/run_maintenance.py`: bounded unattended semantic distillation using Codex CLI.
- `scripts/metered_codex.py` + `scripts/token_report.py`: A/B usage measurement.
- Codex Memories: optional short/medium-term recall layer; not the authoritative rules store.

## Quick start

```bash
python scripts/aios.py validate
python -m unittest discover -s tests -v
python scripts/aios.py add-candidate \
  --title "Example lesson" \
  --summary "A reusable lesson discovered in work." \
  --domain "engineering" \
  --tags "example" \
  --evidence "project://example"
python scripts/aios.py search "example lesson" --limit 3
```

## Codex setup

Run once from this repository:

```bash
python scripts/install.py
```

The installer preserves unrelated `~/.codex/AGENTS.md` content, keeps prior skill backups, installs/symlinks the skills globally, and merges the AIOS user-level hooks into `~/.codex/hooks.json` without removing unrelated handlers. Then open Codex and use `/hooks` to review and trust the hooks.

Optional short/medium-term recall:

```toml
[features]
memories = true
```

Keep this repository private if it will contain personal/project knowledge. Raw session captures remain under ignored `runtime/`; aggregate local token measurements under `metrics/*.jsonl` are ignored as well.

## Important boundary

This system does not claim that storing GitHub knowledge directly increases prompt-cache hit rate. The primary savings mechanism is less repeated searching, reading, tool use, and re-reasoning; progressive disclosure also keeps unnecessary knowledge out of context.

## Automatic maintenance

After normal Codex work accumulates captures, run or schedule:

```bash
python scripts/run_maintenance.py --max-sessions 5
```

See `docs/AUTOMATION.md` for the daily/weekly lifecycle.
