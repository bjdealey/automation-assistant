# Ingest grants CONFIRMED only for attested real exports

**Context**: The learning loop ingests bot JSON and records facts under the confidence taxonomy. `CLAUDE.md:179-182` said "the first real bot JSON provided — a paste counts — promotes the schema INFERRED→CONFIRMED", but `knowledge/README.md` defines corpus-derived facts as OBSERVED and reserves CONFIRMED for documentation, observed UI, or a validated export. A raw paste cannot satisfy both.

**Decision**: An ingest lands facts as OBSERVED by default. It may grant CONFIRMED only when a human attests the JSON is a genuine Control Room export — a validated source under the taxonomy — and only for the structural facts that export directly evidences. Accumulating OBSERVED facts never reaches CONFIRMED on its own.

**Why**: Provenance, not paste-count, is what makes JSON ground truth. This keeps the core trust rule intact — an existing bot stays evidence, not authority — while still letting a genuine export firm up the schema. The generate→import→re-export→diff round-trip remains a separate, stronger bar that confirms bot *generation* (skill 05), not schema observation.

**Consequences**:
- The loop needs one new human input — a provenance attestation per ingest.
- `CLAUDE.md:179-182` must be corrected to match: a paste promotes to OBSERVED; CONFIRMED requires attestation.
