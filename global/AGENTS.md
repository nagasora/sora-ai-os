# Personal Codex operating rules

## Goal
Improve future work by reusing verified knowledge before repeating research, while keeping always-loaded context small.

## Knowledge-first routing
1. Before broad external research, search the personal knowledge store when prior work may be relevant.
2. Load at most 3 highly relevant entries first. Read more only when those entries point to necessary evidence.
3. Prefer verified patterns, decisions, failures, and playbooks over raw candidates.
4. If internal knowledge is insufficient or stale, research externally and record only durable reusable lessons.
5. Never paste the whole knowledge repository into context.

## Evidence and promotion
- `candidate`: one observation; never treat as a universal rule.
- `pattern`: reproduced or strongly evidenced across contexts.
- `decision`: a deliberate choice plus rationale and revisit condition.
- `failure`: a confirmed failure mode with detection and prevention.
- `playbook`: a stable repeatable workflow.
- Promote knowledge only when evidence justifies it; otherwise keep it as a candidate.

## Token discipline
- Search narrow before reading broad.
- Read summaries before source detail.
- External GitHub/web research should be bounded: shortlist first, deep-read only top candidates.
- Do not spawn subagents for small tasks; each subagent has separate model/tool cost.
- Prefer deterministic scripts for indexing, filtering, validation, and repetitive transforms.
- Keep final task context focused on requirements, decisions, and results; avoid raw logs unless needed.

## Learning discipline
Capture durable knowledge only when the task produced at least one of:
- confirmed root cause + fix,
- reusable architecture/implementation decision,
- reproducible experiment/Kaggle result,
- externally researched pattern with evidence,
- repeated failure/prevention rule.
Do not save trivial edits, transient paths, secrets, raw logs, or guesses.

## Development conventions
- Prefer functions/classes for reusable logic.
- Implementation code explains How through structure and naming.
- Tests state What behavior is guaranteed.
- Commit messages explain Why the change exists.
- Code comments are reserved for Why not: rejected alternatives, non-obvious constraints, or hazards.
