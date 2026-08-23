from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def main() -> int:
    """How: aggregate metered tasks by AIOS/baseline mode so token-efficiency claims stay measurable."""
    parser = argparse.ArgumentParser(description="Summarize AIOS metered Codex usage")
    parser.add_argument("--label", default=None)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = root / "metrics" / "task-usage.jsonl"
    if not source.exists():
        print("No metered task data yet.")
        return 0

    groups: dict[str, list[dict]] = defaultdict(list)
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if args.label and record.get("label") != args.label:
            continue
        groups[str(record.get("mode", "unknown"))].append(record)

    for mode in sorted(groups):
        records = groups[mode]
        sums = defaultdict(int)
        ratios = []
        for record in records:
            usage = record.get("usage") or {}
            for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens"):
                sums[key] += int(usage.get(key, 0) or 0)
            if record.get("cached_input_ratio") is not None:
                ratios.append(float(record["cached_input_ratio"]))
        print(f"[{mode}] runs={len(records)}")
        print(f"  input_tokens={sums['input_tokens']}")
        print(f"  cached_input_tokens={sums['cached_input_tokens']}")
        print(f"  output_tokens={sums['output_tokens']}")
        print(f"  reasoning_output_tokens={sums['reasoning_output_tokens']}")
        if ratios:
            print(f"  mean_cached_input_ratio={sum(ratios) / len(ratios):.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
