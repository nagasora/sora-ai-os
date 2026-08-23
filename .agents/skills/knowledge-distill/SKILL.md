---
name: knowledge-distill
description: Distill durable reusable knowledge from a completed coding, debugging, research, Kaggle, or design task into the personal Knowledge OS. Use only when there is a confirmed reusable lesson, decision, failure mode, or reproducible result.
---

# Knowledge Distill

## Eligibility
Save only if the work produced durable value beyond the current task.
Reject secrets, raw logs, guesses, temporary paths, copied source text, and trivial edits.

## Classification
- `candidate`: first observation or unreplicated lesson.
- `decision`: deliberate choice with rationale and revisit condition.
- `failure`: confirmed failure mode with root cause, detection, prevention.
- `pattern`: reproduced across at least 2 independent contexts or supported by strong external evidence.
- `playbook`: stable repeatable procedure with successful use and validation steps.

## Required fields
`id`, `type`, `title`, `summary`, `domain`, `status`, `confidence`, `observed_count`, `created`, `last_verified`, `tags`, `evidence`.

## Procedure
1. Search for semantically similar entries before creating a new one.
2. Update/merge instead of duplicating whenever possible.
3. Write the smallest self-contained lesson that can change a future decision.
4. Link evidence to project paths, commits, issues, papers, or URLs rather than copying raw material.
5. Run `python scripts/aios.py validate` after writing.
