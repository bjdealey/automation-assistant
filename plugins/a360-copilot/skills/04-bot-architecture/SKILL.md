---
name: 04-bot-architecture
description: Convert a natural-language automation idea into a concrete engineering specification and a staged bot design before any JSON is written. Use when the user describes a bot they want ("build a bot that…"), or when requirements are vague and need to be turned into inputs, outputs, decisions, loops, exceptions, and failure handling. Produces a spec with explicitly labelled assumptions; does not jump straight to JSON.
---

# 04 · Bot architecture

**Goal:** produce an engineering specification and staged design from a
requirement — the bridge between natural language and JSON. **Never jump from a
vague requirement directly to JSON.**

## When to use

- The user describes an automation in prose.
- Requirements are incomplete and need structuring before implementation.

## Elicit / determine

Business objective · trigger · inputs · outputs · systems involved · data
sources · transformations · decisions · loops · exceptions · failure conditions ·
retry requirements · logging requirements · security requirements · human
intervention points · expected scale · performance considerations.

If a material requirement is missing, either **ask a targeted question** (only
those that change the design) or **state a labelled assumption** and proceed.

## Decompose into stages

```
INPUT → VALIDATE → INITIALISE → ACQUIRE DATA → PROCESS → DECIDE
→ PERFORM ACTION → VERIFY → ERROR HANDLING → CLEANUP → OUTPUT
```

For each stage note: what it does, the actions/packages likely involved (tag
confidence — the exact actions may need `01`/`02`), the variables it reads and
writes, and how it can fail.

## Design decisions to make explicit

- Decomposition into sub-bots (single responsibility; reuse existing shared
  components found via `03`).
- Error-handling and retry strategy (align to `knowledge/best-practices/`).
- Restartability / idempotency for scale.
- Logging and observability points.
- Credential and sensitive-data handling.

## Output (the spec)

1. Understanding · 2. Assumptions (labelled) · 3. Staged architecture ·
4. Inputs/outputs contract · 5. Sub-bot breakdown · 6. Risks ·
7. Open questions.

Hand off to `05-bot-generation` only once the spec is agreed and the schema
confidence is good enough to generate against.
