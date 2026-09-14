# a360-copilot

The **A360 Bot Engineering Copilot** as an installable Claude Code plugin — 15
composable skills for working on Automation Anywhere A360 bots, under a strict
confidence-tagging discipline (`CONFIRMED` / `OBSERVED` / `INFERRED` / `UNKNOWN`)
and a "never invent JSON fields" rule.

## Install

From Claude Code:

```
/plugin marketplace add bjdealey/automation-assistant
/plugin install a360-copilot@automation-assistant
```

- `add` reads the marketplace from the repo's **default branch**, so the
  marketplace must be committed there (see the repo root `.claude-plugin/marketplace.json`).
- After install, skills are namespaced by the plugin: invoke explicitly with
  `/a360-copilot:<skill>` (e.g. `/a360-copilot:08-bot-review`), and
  model-invocable skills also activate automatically when relevant.

## Skills

| Skill | Status |
|-------|--------|
| `01-platform-discovery` | pending (needs Control Room access) |
| `02-a360-json-schema` | live |
| `03-bot-corpus-analysis` | pending (needs a bot corpus) |
| `04-bot-architecture` | live |
| `05-bot-generation` | pending (draft-only until schema CONFIRMED) |
| `06-bot-validation` | partial (verdict caps at "LIKELY VALID (unverified)") |
| `07-troubleshooting` | live |
| `08-bot-review` | live |
| `09-bot-refactoring` | live |
| `10-bot-documentation` | live |
| `11-dependency-analysis` | live |
| `12-testing` | live |
| `13-security-review` | live |
| `14-performance-review` | live |
| `15-change-impact-analysis` | live |

`live` = works today on bot JSON you paste in · `partial` = works, but a firm
verdict waits on ground truth · `pending` = needs an asset not bundled here
(Control Room UI access, a bot corpus, or a `CONFIRMED` schema).

## Scope & limits (deliberate)

- **Offline advisor.** The skills reason over bot JSON you provide; they do not
  talk to a live Control Room.
- **Schema is `INFERRED`.** A360 bot-JSON structure has not been validated
  against a real export, so generation (05) and validity verdicts (06) are
  **draft-only** and always labelled unverified.
- **Deterministic `a360tools` utilities ship with this plugin** under
  `scripts/a360tools/` (standard library only, no dependencies). Skills that use
  them run `cd "${CLAUDE_PLUGIN_ROOT}/scripts"` first, then
  `python -m a360tools <command>`. They are read-only signals; the skills still
  work as methodologies if you prefer not to run them.

See the source repo's `CLAUDE.md` for the full operating model.
