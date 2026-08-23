---
name: research-before-build
description: Plan a new app, system, feature, or technical architecture by checking internal knowledge first, then a bounded GitHub/official-docs shortlist before implementation. Do not use when implementation direction is already approved and current.
---

# Research Before Build

## Gate
Do not create implementation files until the architecture/MVP plan is accepted or the user explicitly asked for implementation in the same task.

## Workflow
1. Clarify requirements from available context without re-asking known facts.
2. Search internal Knowledge OS first.
3. If external research is still needed, discover at most 5 candidate projects/resources using metadata first.
4. Shortlist at most 3 for deeper reading.
5. For each shortlisted project capture: solved problem, architecture, stack, maintenance/activity, testing, license, reusable ideas, hazards.
6. Classify lessons as `USE`, `ADAPT`, or `AVOID`.
7. Propose technology choices, architecture, MVP boundary, risks, test strategy, and implementation sequence.
8. Record durable external lessons as candidates only after evidence is linked.

## Token policy
Do not clone/read entire repositories by default. Start from README, architecture docs, manifests, top-level tree, and the smallest relevant core files.
