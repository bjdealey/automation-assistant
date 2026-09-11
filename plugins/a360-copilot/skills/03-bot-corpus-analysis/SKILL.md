---
name: 03-bot-corpus-analysis
description: Inventory and analyse a master folder of existing A360 bots to learn the organisation's vocabulary, conventions, reusable components, and patterns vs anti-patterns. Use when the user provides a folder/corpus of bots, asks "what patterns do we use", "document our bots", or wants a baseline before designing or reviewing. Builds an inventory first, classifies every recurring pattern, and never assumes existing = correct.
---

# 03 · Bot corpus analysis

**Goal:** turn a folder of existing bots into structured, classified knowledge —
without assuming any existing bot is correct.

## When to use

- The user supplies a master folder / repository of `.bot` files.
- You need the organisation's naming, variable, error-handling, and logging
  conventions before designing (`04`) or reviewing (`08`).

## Method — inventory before conclusions

1. **Crawl & inventory** (deterministic, first):
   ```bash
   cd tools
   python -m a360tools inventory <corpus_dir> --json > ../knowledge/bots/_inventory.json
   ```
   Establish: folder structure, file types, per-bot action/package usage,
   variable usage, repeated structures.
2. **Per bot**, capture (template in `knowledge/bots/README.md`): purpose,
   inputs, outputs, workflow stages, actions used, variables, external
   dependencies (`a360tools deps`), error handling, logging, risks, reusable
   patterns, potential anti-patterns, complexity (`a360tools complexity`).
3. **Learn the vocabulary:** naming and variable conventions, shared sub-bots,
   folder organisation → record under `knowledge/organisation/`, citing the bots
   that evidence each convention and how consistently it holds.

## Classify every recurring pattern

Existing bot ≠ correct implementation. Tag each pattern:

`platform-confirmed` · `organisation-convention` · `repeated-but-unverified` ·
`potential-anti-pattern` · `best-practice-candidate` · `legacy-pattern`

→ patterns to `knowledge/patterns/`, traps to `knowledge/anti-patterns/`.

## Output

- `knowledge/bots/_inventory.json` + per-bot notes.
- New/updated `knowledge/organisation/`, `patterns/`, `anti-patterns/` entries.
- A short summary: what the org does well, what is risky, what is reusable.

## Guardrails

- Findings from bots are `OBSERVED` until independently validated.
- Do not commit exports containing secrets/PII (see `knowledge/bots/README.md`).
