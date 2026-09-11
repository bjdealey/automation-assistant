---
name: 10-bot-documentation
description: Produce clear documentation for an A360 bot — purpose, inputs/outputs, workflow stages, actions and packages used, dependencies, error handling, logging, and risks. Use when asked to document a bot, explain what a bot does, or generate a README/runbook for a bot. Generates the factual material deterministically with a360tools and labels anything inferred.
---

# 10 · Bot documentation

**Goal:** make a bot understandable to someone who did not write it — accurately,
with inferred parts labelled.

## What to document

- **Purpose** — what business outcome it produces.
- **Trigger** — how it starts (schedule / event / manual), if known.
- **Inputs / Outputs** — the variable contract.
- **Workflow stages** — input → … → output narrative.
- **Actions & packages used** — from `a360tools extract`.
- **Dependencies** — apps, files, credentials, sub-bots, systems (from
  `a360tools deps`; see `11-dependency-analysis`).
- **Error handling & recovery** — what happens on failure.
- **Logging & observability** — what it records and where.
- **Assumptions & preconditions** — environment, data, permissions.
- **Risks / known issues** — from `08-bot-review` if available.
- **Metrics** — complexity from `a360tools complexity`.

## Generate the raw facts deterministically

```bash
cd tools
python -m a360tools extract    <bot_file>
python -m a360tools deps       <bot_file>
python -m a360tools complexity <bot_file>
```

## Output

A single Markdown document (a runbook). Save per-bot notes under
`knowledge/bots/`. Anything not directly evidenced by the JSON is labelled
`INFERRED` (e.g. business purpose deduced from names/comments).

## Guardrail

Do not state a purpose or behaviour the JSON does not support. If the intent is
unclear from the bot, say so and ask, or mark it `INFERRED`.
