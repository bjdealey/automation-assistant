---
name: 01-platform-discovery
description: Systematically inspect the Automation Anywhere A360 Control Room / bot editor to map GUI concepts to their stored JSON and runtime behaviour. Use when exploring the A360 interface, discovering packages, actions, variables, triggers, run/deploy configuration, or when you need to establish "what does this UI control actually store". Records findings into knowledge/platform with source + confidence tags.
---

# 01 · Platform discovery

**Goal:** build a conceptual map from A360's graphical bot representation to its
stored JSON and runtime behaviour — and record it as reusable knowledge.

Do **not** merely browse visually. For every element, establish the chain:

```
GUI concept → GUI control → stored representation → JSON property
→ JSON data type → valid values → runtime behaviour
```

## When to use

- You have access to (or screenshots / exports from) the A360 Control Room.
- You need to know how a specific action, field, variable type, or trigger is
  configured and how it is stored.
- You are building the ground truth that `02-a360-json-schema` depends on.

## Method

1. Pick a target: bot creation, a package's action, a variable type, a trigger,
   run configuration, error handling, sub-bot calls, deployment, or versioning.
2. Observe the UI: available fields, which are required vs optional, defaults,
   allowed values, and dependencies between fields.
3. Get the stored form: export the bot (or use a Git-backed export) and open the
   `.bot` JSON. Normalise it with `python -m a360tools normalize <file>`.
4. Correlate UI ↔ JSON: which JSON keys/values change when you change each field?
5. Note runtime implications and validation rules the UI enforces.

## Record each discovery (to `knowledge/platform/`)

Use the entry template in `knowledge/README.md`, capturing:

- Human-readable name · purpose · parent package/action
- Fields: required / optional · data types · defaults · allowed values · deps
- JSON representation · runtime implications · validation rules
- **Source + confidence** (prefer `CONFIRMED`: docs+version or observed UI/export)

## Output & hand-off

- New/updated files under `knowledge/platform/` (and `knowledge/schema/` when the
  discovery clarifies the JSON model).
- Every schema clarification should also update `knowledge/schema/a360-bot-json.md`
  and, where relevant, an `a360tools` extractor + its test.

## Guardrails

- Never generalise one environment's behaviour to "all A360" — note the version.
- Distinguish what the UI *enforces* from what the JSON merely *permits*.
