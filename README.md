# Automation Assistant — A360 Bot Engineering Copilot

An engineering copilot for **Automation Anywhere A360** bots. It helps you
understand, design, build, validate, troubleshoot, review, refactor, document,
and manage bots — grounded in three sources of knowledge:

1. **Platform knowledge** — A360 documentation, UI behaviour, and validated JSON.
2. **Organisational knowledge** — your own bots, conventions, and components.
3. **Engineering best practice** — reliability, maintainability, security,
   observability, testability, performance.

It treats existing bots as *evidence*, not as proof of correctness, and it never
presents a guess as an A360 fact.

> **Current scope:** a **solo, offline advisor** — it reasons over bot JSON you
> paste or drop in (review, troubleshoot, document, dependency/impact). It does
> not talk to a live Control Room. Bot-JSON *generation* (skill 05) and a firm
> validity *verdict* (skill 06) are **experimental / draft-only** until the
> schema is `CONFIRMED` from a real export. See §"Current scope" in `CLAUDE.md`.

## What's here

| Path | Purpose |
|------|---------|
| [`CLAUDE.md`](CLAUDE.md) | The operating manual — read this first. |
| [`.claude/skills/`](.claude/skills/) | 15 composable copilot skills (`01-…`–`15-…`). |
| [`knowledge/`](knowledge/) | The source-tagged knowledge base (platform, schema, patterns, org, bots, …). |
| [`tools/`](tools/) | `a360tools` — deterministic Python utilities for corpus analysis. |

## Core principles (see `CLAUDE.md` for the full set)

- **Label confidence.** Every non-trivial claim is `CONFIRMED`, `OBSERVED`,
  `INFERRED`, or `UNKNOWN`.
- **Never invent JSON fields.** Unverifiable JSON is marked unverified.
- **Existing ≠ correct.** Corpus patterns are classified, not trusted.
- **Version awareness.** Identify the A360 version; don't over-claim compatibility.
- **Validate before presenting generated JSON.**
- **Tools are deterministic and auditable.**

## Quick start

```bash
# Analyse a folder of exported bots
cd tools
python -m a360tools inventory /path/to/bot/corpus --json

# Run the tool test suite
python -m pytest -q
```

Then read `CLAUDE.md`, add real exported bots under `knowledge/bots/`, and start
validating the schema working model in `knowledge/schema/a360-bot-json.md`
against your environment.

## Status

Working scaffold, honest about its limits. The 15 skills and `a360tools` are in
place and the tests pass — but the schema working model in
`knowledge/schema/a360-bot-json.md` is `INFERRED`, and the test fixture
(`tools/tests/fixtures/hypothesis_bot.json`) encodes a *hypothesis*, not a
confirmed schema. **The first real bot you provide (a paste counts) is the
trigger** to promote the schema to `CONFIRMED`, tighten the extractors, and add
a real fixture. Until then, treat schema/generation/verdict output as unverified.
