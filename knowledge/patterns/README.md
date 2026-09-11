# knowledge/patterns/

Reusable implementation patterns observed or recommended for A360 bots
(e.g. queue-driven processing, retry-with-backoff, config-at-top,
init/cleanup pairing, structured logging).

**Every pattern is classified** — a pattern being common does not make it
correct:

- `platform-confirmed` — relies only on `CONFIRMED` platform behaviour.
- `organisation-convention` — how this org does it.
- `repeated-but-unverified` — seen often, correctness not established.
- `best-practice-candidate` — aligns with `../best-practices/`.
- `legacy-pattern` — historical; may have a better modern approach.

Entry template (per pattern):

```markdown
# Pattern: <name>
**Classification:** <one of the above>
**Problem it solves:** …
**Structure:** … (stages / actions involved)
**When to use / avoid:** …
**Example:** <bot path or minimal illustration>
**Confidence & source:** …
```
