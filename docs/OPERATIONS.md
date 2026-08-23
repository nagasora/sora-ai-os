# Operations

## Daily workflow
1. Work normally in Codex.
2. Before broad research, use `$knowledge-first` or let it trigger implicitly.
3. For new systems use `$research-before-build`.
4. Durable lessons are written as candidates/decisions/failures; trivial work is discarded.
5. SessionEnd captures raw local transcripts into `runtime/inbox/` only; they are never committed.

## Maintenance workflow
Run `$knowledge-maintenance` daily or weekly depending on activity.

Maintenance should:
- process pending captures,
- create/merge only durable candidates,
- promote repeated evidence,
- mark stale knowledge,
- delete processed raw captures,
- validate the repository.

## Git workflow
- `main` contains reviewed durable knowledge.
- Knowledge changes should be small commits whose message explains why a future agent needs the information.
- Raw transcripts, logs, secrets, and copied third-party source text stay outside Git.

## Recommended review cadence
- Every active day: automatic/local capture only.
- Daily or every 2-3 days: batch distillation if work volume is high.
- Weekly: dedupe + promotion + staleness review.
- Monthly: token/quality metrics review and routing-rule cleanup.

## Fully automatic daily distillation
Use Windows Task Scheduler / cron / a ChatGPT desktop scheduled local-project task to run:

```bash
python scripts/run_maintenance.py --max-sessions 5
```

Keep weekly promotion review human-gated even if daily candidate capture is automatic.
