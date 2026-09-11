---
name: 12-testing
description: Design a test strategy and concrete test cases for an A360 bot — happy paths, unhappy paths, edge cases, fixtures, side-effect isolation, and regression checks. Use when asked how to test a bot, to validate a change, or to define acceptance criteria. Complements bot generation, refactoring, and troubleshooting by defining how to prove a bot works.
---

# 12 · Testing

**Goal:** define how to prove a bot does what it should — and keeps doing it
after changes.

## Identify what to test

- **Happy path(s):** the intended flow with representative inputs.
- **Unhappy paths:** each failure condition from the spec (`04`) / review (`08`)
  — missing data, locked file, app not responding, timeout, bad input.
- **Edge cases:** empty inputs, large inputs, boundary values, duplicates,
  special characters, locale/date formats.
- **Decisions & loops:** each branch of every condition; zero / one / many
  iterations.

## Design the tests

For each case record: **precondition / input → action → expected result**.
Prefer **deterministic fixtures** (sample files, seeded data). Isolate side
effects so tests don't mutate production systems (use test folders, test
accounts, dry-run modes).

## Validation & regression

- After a change (`09`), re-run the cases the change touches plus a regression
  set of previously-passing cases.
- Tie diagnosed failures (`07`) to a regression test so the bug can't return.

## Output

- A test plan: cases table + fixtures needed + how to isolate side effects.
- Acceptance criteria for the change / bot.

## Guardrail

Note which tests can be automated vs. which need a human/observed run in a
Control Room, and be explicit about test-environment prerequisites.
