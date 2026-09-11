---
name: 02-a360-json-schema
description: Work with the Automation Anywhere A360 bot JSON schema — read it, reverse-engineer GUI-to-JSON mappings, and answer "what is the valid JSON structure for this action/variable/package". Use whenever bot JSON structure, action/package/command identifiers, attributes, variable references, or expression syntax are in question. Enforces the rule: never invent JSON fields; mark anything unverified.
---

# 02 · A360 JSON schema

**Goal:** be the reliable reference for the shape of A360 bot JSON, and grow that
reference from evidence.

The canonical working model is **`knowledge/schema/a360-bot-json.md`**. It is
currently `INFERRED` — treat it as a hypothesis to validate, not fact.

## When to use

- Reading or explaining a bot's JSON structure.
- Determining the valid JSON for an action, variable, or package.
- Reverse-engineering a GUI action into JSON (pair with `01-platform-discovery`).
- Before `05-bot-generation` (to know the target shape) and during
  `06-bot-validation`.

## Core rules

1. **Never invent JSON fields, action ids, package names, or values.** If it is
   not confirmed, say so and tag it `INFERRED`/`UNKNOWN`.
2. **Prefer the user's own exports** over anything from memory.
3. **Version matters** — the same construct can differ across A360 versions.

## Reverse-engineering method (GUI ↔ JSON)

When you have both a GUI example and its exported JSON:

1. Identify the action in the UI (package + command + configured fields).
2. Locate the corresponding node in the JSON.
3. Map each UI field to its JSON key, data type, and value encoding
   (literal vs variable reference vs expression).
4. Record: action identifier, package identifier, command identifier, required
   vs optional properties, variable-reference syntax, input/output relationships,
   ordering / parent-child rules.
5. Promote the relevant lines in `a360-bot-json.md` from `INFERRED` to
   `CONFIRMED`, citing the export, and tighten the matching `a360tools` extractor.

## Output

- An accurate, confidence-tagged answer about the schema, **or**
- An explicit statement that the structure is unverified and what evidence would
  confirm it.
