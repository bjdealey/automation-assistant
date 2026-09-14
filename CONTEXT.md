# A360 Bot Engineering Copilot

The shared language of this repo: an offline advisor whose reliability grows as validated observations about A360 bots accumulate in a source-tagged knowledge base. This glossary is the canonical vocabulary; the operating manual is [CLAUDE.md](./CLAUDE.md).

## Language

### Confidence

**OBSERVED**:
A fact seen in supplied bots, but not independently validated. A *parallel* source tag to CONFIRMED, not a rung below it — accumulating OBSERVED facts never reaches CONFIRMED on its own.
_Avoid_: verified, proven, "seen in the wild".

**CONFIRMED**:
A fact established from A360 documentation, directly observed UI behaviour, or a genuine validated export. Reached only through one of those sources, never by piling up OBSERVED.
_Avoid_: validated, certain, ground-truth (that names the *source*, not the tag).

**Promotion**:
Raising a fact's confidence tag, appending the new evidence and its source rather than overwriting. Any move *to* CONFIRMED, and any change to code or skills, is human-gated.
_Avoid_: upgrade, verify.

**Provenance**:
Whether ingested bot JSON is a genuine Control Room export or hand-authored / unknown. A human attestation of provenance is what lets an ingest grant CONFIRMED rather than OBSERVED (see [ADR-0001](./docs/adr/0001-ingest-confirms-only-attested-exports.md)).
_Avoid_: origin, source (that names the taxonomy field).

### The loop

**Ingest**:
The single explicit action that feeds bot JSON — a paste or a corpus folder — through deterministic extraction and lands the facts it yields as OBSERVED in the knowledge base. Never fires as a silent side effect of another skill.
_Avoid_: import, load, upload, absorb.

**Learning loop**:
The automated span from an ingest to an updated knowledge base — the part that is currently manual prose in skill 03. The mechanism by which ingesting bots makes the plugin better over time.
_Avoid_: feedback loop, self-improvement, training.

**Corpus**:
The collection of real bot exports the org has ingested, kept local and out of version control. Evidence of how the org *currently* builds bots — not authority on how it *should*.
_Avoid_: dataset, sample, library.

### Payoffs

**Schema fidelity**:
How closely the working model of A360 bot JSON matches real exported bot JSON. Payoff #1 of the learning loop, and the gate on trustworthy generation and validation.
_Avoid_: schema accuracy, correctness.

**Org fingerprint**:
The organisation's learned vocabulary, conventions, and recurring patterns and anti-patterns. Payoff #2 — the second consumer of the same ingested corpus, not a parallel track.
_Avoid_: house style, org profile, conventions (too narrow).
