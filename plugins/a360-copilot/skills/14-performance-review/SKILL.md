---
name: 14-performance-review
description: Find performance and efficiency problems in an A360 bot — unnecessary loops, excessive UI interaction, repeated operations, inefficient data handling, and needless application launches. Use when a bot is slow, when asked to optimise a bot, or as part of a broader review. Uses a360tools complexity metrics and recommends the smallest changes that preserve behaviour.
---

# 14 · Performance review

**Goal:** make a bot faster/leaner without changing what it produces.

## What to look for

- **Loops:** work done inside a loop that could be hoisted out (invariant reads,
  repeated lookups, repeated app launches). Unnecessary nested loops.
- **UI interaction:** screen automation where a `CONFIRMED` API / direct data
  operation exists; excessive click/type steps.
- **Repeated operations:** re-reading the same file/source multiple times;
  recomputing the same value.
- **Data handling:** row-by-row processing where a bulk operation is available;
  loading more data than needed.
- **Application lifecycle:** launching/closing an app per iteration instead of
  once; leaving apps/sessions open (leaks).
- **Waits:** fixed sleeps that dominate runtime (also a reliability issue → `08`).

## Objective signals

```bash
cd "${CLAUDE_PLUGIN_ROOT}/scripts" 2>/dev/null || cd tools   # installed plugin, else this repo
python -m a360tools complexity <bot_file>   # node count, nesting depth, loops, etc.
```

Use metrics to locate hotspots (deep nesting, high node counts inside loops), not
as a verdict on their own.

## Output

- Findings in the `08` format, each with an estimated impact (high/med/low) and
  the smallest change that preserves behaviour.
- Note any change that alters behaviour or risk (→ `09` + `15` + `12`).

## Guardrail

Never trade correctness or reliability for speed silently. If an optimisation
changes error handling or ordering, flag it and validate (`12`).
