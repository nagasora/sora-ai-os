---
name: token-audit
description: Measure whether AI Knowledge OS routing actually reduces Codex usage by comparing labeled metered tasks, cached-input ratio, repeated research, and quality. Use for monthly optimization or A/B checks, not normal execution.
---

# Token Audit

1. Compare the same task class and roughly comparable project state.
2. Use `scripts/metered_codex.py --baseline` for a no-user-config baseline and normal mode for AIOS.
3. Compare at least 5 runs per task class before drawing a conclusion.
4. Track `input_tokens`, `cached_input_tokens`, `output_tokens`, `reasoning_output_tokens`, external-search/tool count when available, and task quality/rework.
5. Do not infer causality from cached-input ratio alone; AIOS is primarily intended to reduce repeated search/read/reasoning and context pollution.
6. If AIOS mode uses more tokens without improving quality, inspect over-broad retrieval, too many skills, unnecessary subagents, or noisy global instructions.
