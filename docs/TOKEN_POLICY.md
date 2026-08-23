# Token policy

## Context budget
- Global AGENTS: target 2-4 KB; hard goal under 8 KB.
- Initial knowledge retrieval: max 3 entries.
- Search result summaries: target <= 250 words total.
- Deep entry reads: only after relevance is established.
- External repository discovery: max 5 candidates, max 3 deep reads.
- Raw logs/transcripts: never inject wholesale; summarize/filter deterministically first.

## Search order
1. Current repo docs and explicit user requirements.
2. Curated personal Knowledge OS.
3. Past project/decision/failure evidence.
4. External GitHub / official docs / papers only for missing or stale knowledge.

## Subagents
Use for independent read-heavy exploration when the time/quality benefit is material. Avoid for small tasks because each subagent performs separate model/tool work.

## Measurement
For metered non-interactive runs, `codex exec --json` exposes `input_tokens`, `cached_input_tokens`, `output_tokens`, and `reasoning_output_tokens`. Compare workflows using the same task class rather than relying on one anecdotal run.

## A/B measurement
Run comparable tasks through:

```bash
python <AIOS_HOME>/scripts/metered_codex.py --label <task-class> --baseline "<prompt>"
python <AIOS_HOME>/scripts/metered_codex.py --label <task-class> "<prompt>"
python <AIOS_HOME>/scripts/token_report.py --label <task-class>
```

Use several runs and compare quality/rework as well as token counts. Cached-input ratio alone does not establish that the knowledge layer caused savings.
