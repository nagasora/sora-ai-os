# Personal Codex operating rules

## Cost-efficient agent tree

- Root/orchestrator: `gpt-6-astra`, reasoning `medium`. Own scope, acceptance criteria, integration, verification, and the final response.
- Delegate on demand: `explorer` = `gpt-5.6-luna` / `max` for bounded repository investigation; `worker` = `gpt-5.6-sol` / `high` for implementation and focused tests; `researcher` = `gpt-5.6-luna` / `max` for focused source lookup.
- Only when needed: `reviewer` = `gpt-6-astra` / `xhigh` for independent review after integration, when a concrete correctness/security/concurrency risk or explicit user request justifies it. Self-review is not independent review.
- Split useful work; do not spawn every role. Handle small tasks locally. Delegate only a concrete bounded subtask that can run alongside useful parent work. Keep at most three children active; children must not delegate further.
- Each handoff specifies objective, owned files/read-only scope, acceptance criteria, and required evidence. Never overlap writers or repeat the same investigation. Pass distilled context, not the entire history; when using explicit model overrides, use a fresh or limited-history fork.
- Return findings or changed files, validation evidence, and unresolved risks. Root integrates and verifies proportionately. If a requested model is unavailable, report that limitation rather than silently substituting it.

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
- Use the agent tree only when division of work is useful; every child consumes additional model/tool budget.
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

## Implementation harness

For feature work, bug fixes, and code-changing maintenance, use the `implementation-harness` skill when available. The default operating contract is:

- Fix the smallest complete slice. State the scope, done condition, and out-of-scope items briefly before coding; skip a large plan for a small change.
- Reuse the nearest existing implementation and test. Do not add speculative abstractions, compatibility layers, retries, fallbacks, or unrelated cleanup.
- Test budget: start with one reusable test unit per feature (prefer extending or parameterizing an existing test file). Add a new test file only when the behavior has no natural existing home or is an independent boundary. Add tests for new observable behavior, regressions, or material risk—not for every edit or internal branch.
- After the focused test passes, stop. Run broader suites only when the change crosses module/API/schema/concurrency/security/build boundaries, CI requires them, or the user asks. Do not create another test merely to reduce uncertainty.
- For a GitHub-backed change, completion requires a clean scoped diff, the proportionate validation, and an opened pull request with its URL, summary, validation, and known limitations. Never stage unrelated work, merge the PR, or claim completion without the PR; if remote access or permission blocks it, report `BLOCKED` with the exact missing gate.
- Astra root chooses the risk tier and acceptance condition, delegates bounded implementation to Sol when useful, and integrates and verifies the result.
- During self-review, add a test or broader suite only when a concrete risk or failing behavior justifies it.

Detailed workflow: `.agents/skills/implementation-harness/SKILL.md`.
- For HTML/CSS/Tailwind/React UI work, load `.agents/skills/ui-design-harness/SKILL.md`; select one domain and lock its typography/tokens across the product instead of reusing a generic full-screen template.
