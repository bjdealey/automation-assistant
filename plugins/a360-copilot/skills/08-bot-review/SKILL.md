---
name: 08-bot-review
description: Review an A360 bot across six dimensions — correctness, reliability, maintainability, performance, security, observability. Use when asked to review, critique, or assess the quality of a bot, or to audit it against engineering standards. Produces findings in the fixed form SEVERITY → LOCATION → PROBLEM → WHY IT MATTERS → RECOMMENDED CHANGE → CONFIDENCE, judged against knowledge/best-practices.
---

# 08 · Bot review

**Goal:** assess a bot against engineering standards and report actionable,
prioritised findings. Existing ≠ correct.

## Dimensions

- **Correctness** — logic errors, wrong conditions, variable misuse, race
  conditions, unfounded assumptions, missing validation.
- **Reliability** — missing error handling, fragile selectors, timing
  assumptions, missing retries, unhandled external failures, poor recovery.
- **Maintainability** — duplication, poor naming, excess complexity, monolithic
  workflows, hard-coded values, poor separation of concerns.
- **Performance** — unnecessary loops, excess UI interaction, repeated
  operations, inefficient data handling, needless app launches (→ `14`).
- **Security** — credentials, sensitive data, hard-coded secrets, logging of
  secrets, unsafe file handling (→ `13`).
- **Observability** — logging, status tracking, failure context, diagnostics,
  auditability.

Judge against `knowledge/best-practices/a360-engineering-standards.md`. Use
`a360tools complexity` / `deps` / `validate` for objective signals.

## Finding format (every finding)

```
SEVERITY:  CRITICAL | HIGH | MEDIUM | LOW
LOCATION:  <bot / action / node / variable>
PROBLEM:   <what is wrong>
WHY IT MATTERS: <impact / failure mode>
RECOMMENDED CHANGE: <smallest effective fix>
CONFIDENCE: HIGH | MEDIUM | LOW
```

## Output

- Findings ordered by severity, then confidence.
- A short overall assessment (top risks, quick wins).
- Where a finding is a recurring org pattern, cross-link/record it in
  `knowledge/anti-patterns/`.

## Guardrail

Separate **defects** (will/again cause failure) from **style/preference**; label
which is which, and tag confidence honestly.
