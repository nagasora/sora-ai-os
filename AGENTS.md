# AI Knowledge OS repository guidance

## Agent policy

Use the cost-efficient agent tree in `global/AGENTS.md`. Delegate bounded work on demand; do not spawn every role or allow recursive delegation.

Read `global/AGENTS.md` as the canonical personal operating policy for this repository.

## Repository rules
- `knowledge/` contains curated, Git-tracked durable knowledge.
- `runtime/` contains ephemeral captures and must never be committed.
- Use `python scripts/aios.py search "<query>"` before broad repository reading.
- New observations go to `knowledge/candidates/`; do not directly create a playbook from a single observation.
- Run `python scripts/aios.py validate` after changing knowledge metadata.
- Run `python -m unittest discover -s tests -v` after changing scripts.
