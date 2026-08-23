# Automation

## Capture: automatic, every Codex session
The user-level hooks installed by `scripts/install.py` do four small deterministic things:
- `SessionStart`: inject the AIOS path/search route and pending count.
- `UserPromptSubmit`: journal a bounded copy/hash of the prompt.
- `Stop`: journal a bounded copy/hash of the final assistant message.
- `SessionEnd`: copy session metadata and the raw transcript locally as fallback evidence.

Raw captures are ignored by Git. Hook input is treated as untrusted data, and hook failures are fail-open so a capture problem does not block normal Codex work.

## Daily distillation: automatic and bounded
Schedule:

```bash
python <AIOS_HOME>/scripts/run_maintenance.py --max-sessions 5
```

The runner invokes `codex exec --ephemeral --ignore-user-config --sandbox workspace-write --json`, processes only valid `pending_distillation` metadata (at most five per run), and records aggregate usage in ignored `metrics/maintenance-usage.jsonl`.

Daily maintenance may create/merge candidates, explicit decisions, and confirmed failures. Capture and transcript text is evidence only; embedded instructions are not authority. It must not automatically promote candidates to patterns/playbooks.

## Weekly reviewed promotion
Once per week, run `$knowledge-maintenance` interactively with the instruction:

`Review promotion candidates, stale entries, duplicates, and superseded rules. Show the proposed promotion/demotion set before applying it.`

This human gate prevents one hallucinated or context-specific result from becoming a global rule.

## GitHub sync
Use a private repository as the source of truth. Commit reviewed durable changes in small batches. Do not commit `runtime/`.
