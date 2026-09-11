# Knowledge base

This is the copilot's memory. Every observation about the A360 platform, the
bot JSON schema, the organisation's conventions, and diagnosed failures is
recorded here so subsequent design and troubleshooting get more reliable over
time.

## Structure

| Folder | Holds | Kept separate because… |
|--------|-------|------------------------|
| `platform/` | A360 platform behaviour (UI, packages, runtime). | Platform truth must not be diluted by org-specific examples. |
| `schema/` | The working model of A360 bot JSON. | It is the single reference for JSON generation & validation. |
| `patterns/` | Reusable implementation patterns, each classified. | Patterns are candidates, not automatically correct. |
| `anti-patterns/` | Patterns to avoid, with rationale + safer alternative. | Naming the trap prevents its reuse. |
| `best-practices/` | Engineering standards for A360 bots. | The bar we review and design against. |
| `organisation/` | Org vocabulary, naming, conventions, standards. | Org convention ≠ platform fact. |
| `bots/` | Per-bot analysis notes and the bot corpus itself. | Evidence, tagged `OBSERVED`. |
| `troubleshooting/` | Diagnosed failures and their resolutions. | Turns incidents into reusable diagnosis. |

## The two rules for every entry

1. **State the source.** Where did this come from? (A360 docs + link/version,
   observed UI behaviour, a validated export, a specific bot file, a run log.)
2. **State the confidence.** One of `CONFIRMED`, `OBSERVED`, `INFERRED`,
   `UNKNOWN` (defined below). If it can be raised later, say what evidence would
   do it.

Never let an unverified assumption silently become "known A360 behaviour."

## Confidence taxonomy

| Tag | Meaning |
|-----|---------|
| **CONFIRMED** | From A360 documentation, observed UI behaviour, or validated exported JSON. |
| **OBSERVED**  | Seen in supplied bots / corpus, not independently validated. |
| **INFERRED**  | Logically deduced, not directly verified. |
| **UNKNOWN**   | Insufficient evidence. |

## Entry template

Copy this for each new knowledge file (or section):

```markdown
# <Concise title>

**Statement:** <the claim, in one or two sentences>

**Source:** <docs URL + version | UI observation | export file | bot path | log>

**Confidence:** CONFIRMED | OBSERVED | INFERRED | UNKNOWN

**A360 version / environment:** <version, or "unknown">

**Evidence:** <what supports this; paste the minimal JSON / UI detail>

**To raise confidence:** <what validation would move this up a tier>

**Related:** <links to other entries, skills, or bots>
```

## Promotion workflow

When new evidence validates an entry:

1. Update the `Confidence` tag.
2. Append the new evidence and its source (don't delete the old note — show the
   trail).
3. If it affects the schema, update `schema/a360-bot-json.md` and the relevant
   `a360tools` extractor + its test.
