# Knowledge lifecycle

## States

`candidate -> pattern -> playbook`

Separate durable record types are `decision` and `failure`.

## Promotion rules

### Candidate
One observation, one task, or an externally sourced claim not yet validated in your own work.

### Pattern
Normally requires at least two independent observations plus evidence. A high-quality authoritative source may justify earlier promotion, but record the reason.

### Playbook
A pattern becomes a playbook only after the procedure is repeatable, validation steps are known, and failure/rollback conditions are explicit.

### Stale / superseded
Do not delete history silently. Mark stale assumptions and link newer entries with `superseded_by` when applicable.

## Knowledge quality test
A durable entry should answer: "Would reading this change the next AI's decision or prevent repeated work?" If not, discard it.
