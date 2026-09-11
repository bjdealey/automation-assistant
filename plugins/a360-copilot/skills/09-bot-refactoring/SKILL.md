---
name: 09-bot-refactoring
description: Make a targeted, safe change or improvement to an existing A360 bot without redesigning it. Use when the user asks to fix, tweak, improve, or modify a specific behaviour of an existing bot. Applies the smallest required change, preserves unrelated behaviour, checks dependencies/variables/error handling, and explains exactly what changed. Never silently redesigns a bot when a targeted fix was requested.
---

# 09 · Bot refactoring / improvement

**Goal:** change what needs changing and nothing else. **Never silently redesign
a bot when the user asked for a targeted fix.**

## Process

1. Understand the existing implementation (read the bot; use `03`/`11` if large).
2. Identify the **intended** behaviour.
3. Identify the **current** behaviour.
4. Identify the **smallest required change** to close the gap.
5. Preserve unrelated behaviour.
6. Check dependencies (`11-dependency-analysis`) — is this bot/sub-bot shared?
7. Check variable compatibility (types, inputs/outputs, references).
8. Check error handling around the change.
9. Produce revised JSON where possible, and run `06-bot-validation`.
10. Explain exactly what changed and why.

## If the change is bigger than a targeted fix

Stop and surface it: describe the larger change, its blast radius
(`15-change-impact-analysis`), and let the user decide. Do not expand scope on
your own.

## Output

- **What changed** (a precise, minimal diff description — ideally a structural
  diff via `python -m a360tools diff <old> <new>`).
- **What was deliberately preserved.**
- **Validation status** (`06`).
- **Regression risks** and suggested checks (`12-testing`).

## Guardrail

If the bot or a shared sub-bot has other consumers, a "small" change may not be
small. Verify with `11` before treating it as local.
