---
name: knowledge-first
description: Search and reuse the personal AI Knowledge OS before repeating research, debugging, architecture analysis, experiments, or prior decisions. Use when past work may be relevant; do not use for trivial one-off edits.
---

# Knowledge First

1. Convert the current task into a short retrieval query containing the problem, domain, and important constraints.
2. Use the AIOS search command supplied by SessionStart context and request at most 3 results.
3. Read summaries first. Load a full entry only when it is directly relevant.
4. Rank sources in this order: `playbook` / `pattern` / `decision` / `failure` / `candidate`.
5. Check `status`, `confidence`, `last_verified`, and evidence before relying on an entry.
6. If relevant knowledge is missing, stale, or weak, do bounded external research.
7. Never infer that a candidate is a general rule.

Output a short statement of reused knowledge IDs when they materially affect the task.
