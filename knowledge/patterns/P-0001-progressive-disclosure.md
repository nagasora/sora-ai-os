---
id: "P-0001"
type: "pattern"
title: "Use progressive disclosure for AI knowledge retrieval"
summary: "Keep always-loaded instructions small; retrieve only a few relevant summaries first and deep-read evidence on demand."
domain: "ai-agent-operations"
status: "active"
confidence: "high"
observed_count: "2"
created: "2026-08-19"
last_verified: "2026-08-19"
tags: "codex, context, retrieval, token-efficiency"
evidence: "OpenAI Codex Skills and AGENTS documentation"
---

## Pattern

A small routing layer plus on-demand retrieval preserves context for the current task and avoids repeatedly loading unrelated knowledge.

## Reuse condition

Use this whenever a knowledge corpus or skill catalog is large enough that loading it wholesale would compete with task context.

## Limits

This reduces unnecessary context and repeated work; it does not by itself prove a specific prompt-cache or quota reduction.
