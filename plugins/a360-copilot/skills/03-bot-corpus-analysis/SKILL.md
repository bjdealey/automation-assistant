---
name: 03-bot-corpus-analysis
description: Inventory and analyse existing A360 bots, and run the deterministic ingest loop that turns a pasted bot or a corpus folder into durable, source-tagged knowledge. Use when the user provides a bot or a folder/corpus of bots, says "ingest this", asks "what patterns do we use", "document our bots", or wants a baseline before designing or reviewing. Builds an inventory first, classifies every recurring pattern, never assumes existing = correct, and never mutates the knowledge base without the engineer reviewing a git diff.
---

# 03 · Bot corpus analysis & ingest

**Goal:** turn a bot — one paste or a whole folder — into structured, classified,
source-tagged knowledge, without assuming any existing bot is correct, and
without the knowledge base ever changing silently.

## When to use

- The user hands you a bot (a paste counts) or a master folder of `.bot`/`.json`
  files and wants it recorded — "ingest this", "learn from these".
- You need the organisation's naming, variable, error-handling, and logging
  conventions before designing (`04`) or reviewing (`08`).

**Ingest is always explicit.** It never fires as a side effect of another skill.
Review (`08`), troubleshooting (`07`), and the rest may *offer* "ingest this?" —
they never do it automatically.

## The ingest loop

The deterministic part is a **read-only** `a360tools` command that computes an
ingest *plan*; the plan mutates nothing. You then apply the plan to the working
tree and stop at a `git diff` for the engineer to review and commit. git is the
commit gate, the audit trail, and the rollback — **nothing here auto-commits**.

### 1 · Plan (read-only, deterministic)

Run from `tools/`. Pass the ledger so an already-ingested bot is a no-op.

```bash
cd "${CLAUDE_PLUGIN_ROOT}/scripts" 2>/dev/null || cd tools   # installed plugin, else this repo
# single bot
python -m a360tools ingest-plan <bot.json> --ledger ../knowledge/bots/_ingested.json
# whole corpus folder
python -m a360tools ingest-corpus ../knowledge/bots/corpus --ledger ../knowledge/bots/_ingested.json
```

The plan prints the bot identity (`hash`, name, version), its `provenance`, and
the proposed `knowledge/` entries. This *is* the dry run — read it before
applying anything. A bot whose hash is already in the ledger comes back
`idempotent_noop` with no proposed entries; re-ingesting the same bot changes
nothing.

### 2 · Attest provenance (the gate on CONFIRMED)

Before proposing any `CONFIRMED` entry, ask the engineer one question:

> Is this bot a genuine Control Room **export** (not hand-authored or unknown)?

- **No / unsure →** run without `--attested-export`. Every entry is `OBSERVED`.
  A paste promotes facts to `OBSERVED`, never to `CONFIRMED`.
- **Yes →** add `--attested-export`. Only the **structural** facts the export
  directly evidences become `CONFIRMED`; observational facts stay `OBSERVED`.

Accumulating `OBSERVED` evidence never becomes `CONFIRMED` on its own — only an
attested export does that (see `docs/adr/0001-ingest-confirms-only-attested-exports.md`
and `CONTEXT.md`).

### 3 · Apply the plan to the working tree

For each proposed entry, write it to a topic file under its `target`
(`knowledge/schema/…` for schema facts, `knowledge/organisation/…` for the org
fingerprint), carrying its confidence tag, the A360/package `version`, and the
`evidence` (the bot hash). Then:

- **Ledger:** append each non-noop plan's `ledger_line` to
  `knowledge/bots/_ingested.json` (a JSON object keyed by `hash`), stamping
  `first_seen` with today's date at write time.
- **Per-bot note:** write one `knowledge/bots/<name>.md` per ingested bot from
  the template in `knowledge/bots/README.md`.

Tag facts with the version they were seen in; note a variance across versions
**only when two versions actually differ**, so the schema doc does not fragment
prematurely.

### 4 · Handle contradictions

The tool does mechanical idempotency and entry generation; the semantic
judgement is yours. When a proposed entry meets an existing one:

- **Agrees with an existing entry →** append the new evidence and bump a
  frequency count. Repetition strengthens an entry; it never overwrites it.
- **New `OBSERVED` contradicts a `CONFIRMED` fact →** raise a loud **CONFLICT**
  note for the engineer and **leave the `CONFIRMED` entry untouched**.
  Observation never silently overrides ground truth.
- **Two `OBSERVED` bots disagree →** record **both** with their counts and
  classify the pattern `repeated-but-unverified`, so the disagreement is visible
  instead of one clobbering the other.

### 5 · Stop at the diff

Show `git diff` and stop. The engineer reviews an ordinary diff and commits it
themselves. Do not commit, and do not promote anything to `CONFIRMED`, on their
behalf.

## Classify every recurring pattern

Existing bot ≠ correct implementation. Tag each recurring pattern:

`platform-confirmed` · `organisation-convention` · `repeated-but-unverified` ·
`potential-anti-pattern` · `best-practice-candidate` · `legacy-pattern`

→ patterns to `knowledge/patterns/`, traps to `knowledge/anti-patterns/`,
vocabulary and conventions to `knowledge/organisation/` (cite the bots that
evidence each, and how consistently it holds).

## Output

- Applied `knowledge/` entries (schema + organisation), the updated
  `knowledge/bots/_ingested.json` ledger, and one per-bot note each — all in the
  working tree, uncommitted.
- A short summary: what the org does well, what is risky, what is reusable.

## Guardrails

- Findings from bots are `OBSERVED` until independently validated; `CONFIRMED`
  requires an attested export.
- The plan is read-only; only this skill writes `knowledge/`, and only git
  commits it. Nothing auto-commits; nothing auto-promotes to `CONFIRMED`.
- Real exports are git-ignored (`knowledge/bots/corpus/`). Commit a bot only
  after scrubbing credentials, paths, and PII (see `knowledge/bots/README.md`).

## Dry-run acceptance (manual)

The apply step, the attestation prompt, and the commit gate are agent behaviour
with no unit seam — verify them by hand:

```bash
cd "${CLAUDE_PLUGIN_ROOT}/scripts" 2>/dev/null || cd tools   # installed plugin, else this repo
python -m a360tools ingest-plan tests/fixtures/hypothesis_bot.json
```

Confirm the proposed entries match expectations (structural schema facts + one
organisation usage fact, all `OBSERVED` without `--attested-export`). Apply the
plan, run `git diff`, confirm the diff matches, then `git checkout` to discard it
— the synthetic fixture is not real corpus knowledge.
