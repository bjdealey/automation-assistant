---
name: 07-troubleshooting
description: Diagnose a failing A360 bot from evidence — error messages, logs, JSON, screenshots, variable values, run history. Use when a bot errors, behaves unexpectedly, or "fails when doing X". Follows a disciplined reproduce → localise → hypothesise → rank → smallest-safe-fix process, ranks each diagnosis HIGH/MEDIUM/LOW confidence, and records the resolution to knowledge/troubleshooting.
---

# 07 · Troubleshooting

**Goal:** find the real cause from evidence and recommend the smallest safe fix.
Do **not** suggest random changes.

## Evidence to gather

Error messages · execution logs · bot JSON · screenshots · GUI config ·
variable values · input data · runtime behaviour · previous successful vs failed
runs · relevant A360 docs · environment factors.

## Process

1. Reproduce / characterise the failure (when, how often, deterministic?).
2. Identify the failing action.
3. Identify its inputs and inspect variable values feeding it.
4. Inspect preceding actions (what produced those values?).
5. Inspect dependencies (`11-dependency-analysis`): apps, files, credentials,
   sub-bots, systems.
6. Inspect error handling around the failure.
7. Identify environmental factors (version, machine, permissions, data).
8. Generate hypotheses.
9. Rank hypotheses by likelihood.
10. Identify the evidence that would distinguish them.
11. Recommend the **smallest safe fix**.
12. Explain **why** it should work.
13. Identify regression risks.
14. Suggest validation tests (`12-testing`).

## Confidence

Label each diagnosis **HIGH / MEDIUM / LOW**, and state what evidence would
raise a LOW/MEDIUM one.

## Output & record

- Ranked hypotheses → chosen root cause → smallest fix → why → risks →
  validation.
- Add a `knowledge/troubleshooting/` entry (template there) so the signature is
  reusable next time.

## Guardrail

Correlation is not cause. Prefer the fix supported by the most evidence, not the
first plausible one.
