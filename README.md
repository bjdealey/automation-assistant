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

Scaffold. The skills and tools are in place; the schema working model is
`INFERRED` and must be validated against real exports from your A360
environment before it is relied upon.
