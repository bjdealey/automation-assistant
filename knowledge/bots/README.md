# knowledge/bots/

Two things live here:

1. **The corpus** — real exported `.bot` files (and their folders) you want the
   copilot to analyse. Add them under a subfolder, e.g. `bots/corpus/<name>/`.
2. **Per-bot analysis notes** — one Markdown file per bot capturing what we
   learned. Findings from real bots are tagged `OBSERVED` unless independently
   validated.

> Do not commit exports containing secrets or sensitive data. Scrub first, or
> keep them out of version control (see `.gitignore`). Bot logic tagged
> `OBSERVED` is evidence of how the org builds bots — not proof it is correct.

### Per-bot analysis template

```markdown
# Bot: <name>
**Path:** <corpus path>   **A360 version:** <if known>   **Confidence:** OBSERVED

**Purpose:** …
**Inputs / Outputs:** …
**Workflow stages:** input → … → output
**Actions & packages used:** … (from `a360tools extract`)
**Variables:** …
**External dependencies:** apps / files / credentials / sub-bots / systems
  (from `a360tools deps`)
**Error handling:** …
**Logging:** …
**Risks:** …
**Reusable patterns:** → link `../patterns/`
**Potential anti-patterns:** → link `../anti-patterns/`
**Complexity metrics:** … (from `a360tools complexity`)
```

Generate the raw material with:

```bash
cd tools
python -m a360tools inventory  ../knowledge/bots/corpus --json
python -m a360tools extract    ../knowledge/bots/corpus/<bot>.bot
python -m a360tools deps       ../knowledge/bots/corpus/<bot>.bot
```
