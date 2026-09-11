---
name: 05-bot-generation
description: Generate valid Automation Anywhere A360 bot JSON from an agreed specification. Use when the user asks to produce bot JSON, scaffold a bot, or turn a design into implementation. Generates syntactically valid JSON that follows the confirmed A360 schema, uses only known action/package structures, and never invents fields; always runs the validation pass and reports validity + uncertainties before presenting output.
---

# 05 · Bot generation

**Goal:** produce A360 bot JSON that is syntactically valid and structurally
faithful to the **confirmed** schema — or clearly state where it cannot be.

Never generate pseudo-JSON when the user asks for A360 bot JSON. But equally,
**never present invented structure as valid.**

## Prerequisites

1. An agreed spec (from `04-bot-architecture`).
2. Schema confidence: consult `knowledge/schema/a360-bot-json.md`. If the needed
   structures are still `INFERRED`, you may produce a **best-effort draft** but
   it must be labelled **unverified**, with the specific unverified parts named.
   Prefer generating from confirmed structures / the user's own exports.

## Rules

- Syntactically valid JSON.
- Follow the discovered A360 schema; correct nesting and execution order.
- Valid action/package/command identifiers only — no invented ones.
- Correct variable references and data types.
- Preserve required metadata.
- No unsupported actions or configuration values.

## Process

1. Map each spec stage to actions/packages (tag confidence per item).
2. Define variables (names, types, input/output, defaults) per the org's
   conventions (`knowledge/organisation/`).
3. Assemble nodes in execution order with correct container nesting.
4. Wire variable references and attribute values.
5. **Run `06-bot-validation`** (and `python -m a360tools validate`).

## Output (always in this order)

1. **Design summary** (recap of the spec being implemented)
2. **Assumptions** (labelled)
3. **JSON**
4. **Validation status** (from `06`) — including "verified against schema:
   yes/partial/no"
5. **Known uncertainties** (exactly which fields/values are unverified and why)

## Guardrail

If validity for the target A360 version cannot be established, say so plainly.
A labelled-unverified draft is acceptable; a confident-but-wrong bot is not.
