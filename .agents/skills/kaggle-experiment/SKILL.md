---
name: kaggle-experiment
description: Design, run, and record Kaggle/ML experiments with leakage-safe validation, reproducibility, explicit hypotheses, and reusable experiment lessons. Use for competition modeling and experiment decisions.
---

# Kaggle Experiment

1. Search prior Kaggle/ML knowledge for dataset structure, validation traps, feature/model patterns, and known failures.
2. State hypothesis, expected mechanism, primary metric, validation design, and stopping criterion before coding.
3. Change one important factor per experiment when practical.
4. Record seed, split, data version, features, model/config, score, runtime, and artifact paths.
5. Treat leaderboard gains without trustworthy CV as weak evidence.
6. After the experiment, record result + interpretation + next decision.
7. Distill a durable candidate only when the result changes future experimental choices.
