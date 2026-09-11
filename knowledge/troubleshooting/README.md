# knowledge/troubleshooting/

Diagnosed failures and their resolutions — so each incident becomes reusable
diagnosis. Feeds skill `07-troubleshooting`.

One file per distinct failure signature. Record the evidence chain and the
smallest fix that resolved it, plus how confident we were.

### Template

```markdown
# Failure: <short signature, e.g. "Excel action fails: file locked">

**Symptom / error message:** <verbatim>
**Context:** bot / action / A360 version / environment
**Evidence gathered:** logs, variable values, preceding actions, dependencies
**Hypotheses considered (ranked):**
  1. … (most likely) — distinguishing evidence: …
  2. …
**Root cause:** …
**Smallest safe fix:** …
**Why the fix works:** …
**Regression risks:** …
**Validation performed:** …
**Diagnosis confidence:** HIGH | MEDIUM | LOW
```

Reason from evidence, not guesses. Rank hypotheses, identify the evidence that
distinguishes them, then recommend the smallest safe fix — and say why it should
work and what it might break.
