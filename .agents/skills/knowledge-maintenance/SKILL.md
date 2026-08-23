---
name: knowledge-maintenance
description: Periodically consolidate, deduplicate, age, promote, or archive personal Knowledge OS entries and process pending session captures. Use for scheduled maintenance, not normal task execution.
---

# Knowledge Maintenance

1. Inspect `runtime/inbox/*.json` and their local transcript copies when present.
2. Extract only durable candidate lessons. Do not copy raw transcript text into Git-tracked knowledge.
3. Search for duplicates and merge into existing entries.
4. Increment `observed_count` only for genuinely independent confirmations.
5. In unattended/daily maintenance, never auto-promote a candidate to pattern/playbook. Promotion belongs to a reviewed weekly pass.
6. Weekly promotion policy:
   - candidate -> pattern: normally `observed_count >= 2` plus concrete evidence, or unusually strong authoritative evidence.
   - pattern -> playbook: repeatable steps have succeeded and validation/rollback are known.
7. Downgrade stale entries whose assumptions no longer hold; set `status: stale` rather than silently deleting history.
8. Archive superseded entries and leave `superseded_by` links.
9. Remove processed inbox captures after durable extraction; keep no raw transcripts in Git.
10. Run validation and report counts: created, merged, promoted, stale, archived, discarded.
