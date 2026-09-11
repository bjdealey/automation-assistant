# knowledge/anti-patterns/

Patterns to **avoid**, each with the reason and a safer alternative. Naming a
trap explicitly is what stops it being copied out of the corpus.

Common A360 anti-patterns to watch for (confirm against real bots before
asserting any is present):

- Hard-coded credentials, paths, or URLs inside actions.
- Fixed `sleep`/delay instead of waiting for a condition.
- No error handling around external I/O (files, apps, UI, network).
- Monolithic bots with no sub-bot decomposition.
- Logging of sensitive data (PII, secrets, tokens).
- Re-reading the same data source repeatedly inside a loop.
- Relaunching an application every loop iteration.
- Silent failure (catch that swallows the error with no log / no signal).
- Copy-paste duplication instead of a shared sub-bot.

Entry template (per anti-pattern):

```markdown
# Anti-pattern: <name>
**Why it's harmful:** …
**How to detect it:** … (what to look for in JSON / behaviour)
**Safer alternative:** … (link a `../patterns/` or `../best-practices/` entry)
**Severity (typical):** CRITICAL | HIGH | MEDIUM | LOW
**Confidence & source:** …
```
