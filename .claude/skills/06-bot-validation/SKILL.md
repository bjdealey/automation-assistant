---
name: 06-bot-validation
description: Run the validation pass over generated or edited A360 bot JSON before it is presented or used. Use after any JSON generation (05) or modification (09), or when asked "is this bot JSON valid". Applies an 11-point structural checklist plus the deterministic a360tools validate report, and states an honest validity verdict for the target A360 version.
---

# 06 · Bot validation

**Goal:** establish, and honestly report, whether bot JSON is valid before it is
presented or used.

## When to use

- Immediately after `05-bot-generation` or `09-bot-refactoring`.
- Whenever asked to check a bot's JSON.

## The 11-point checklist

1. **JSON syntax** — parses cleanly (`python -m a360tools validate <file>`).
2. **Schema structure** — matches `knowledge/schema/a360-bot-json.md`.
3. **Action identifiers** — every command is a known action.
4. **Package identifiers** — every package (name+version) is known/declared.
5. **Required properties** — present on every action.
6. **Variable references** — every referenced variable exists.
7. **Variable types** — references are type-compatible with usage.
8. **Parent/child relationships** — containers (If/Loop/Try) nest correctly.
9. **Action ordering** — execution order is coherent (init before use, etc.).
10. **References to nonexistent objects** — no dangling sub-bot / file / var.
11. **Known A360 constraints** — no unsupported values for the target version.

## Deterministic assist

```bash
cd tools
python -m a360tools validate <bot_file>        # heuristic structural report
```

Treat tool output as a **signal**, not a verdict: it is schema-tolerant and
heuristic. A clean report does not by itself prove control-room validity.

## Verdict (report one)

- **VALID (verified)** — checks pass against `CONFIRMED` schema for the known
  version.
- **LIKELY VALID (unverified)** — passes structural checks but the schema/version
  is not fully `CONFIRMED`; name what is unverified.
- **INVALID** — list each failing check with location and fix.

If version compatibility cannot be established, say so — do not overclaim.
