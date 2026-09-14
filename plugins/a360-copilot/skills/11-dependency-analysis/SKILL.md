---
name: 11-dependency-analysis
description: Map an A360 bot's dependencies and build its dependency graph — sub-bots, actions, packages, variables, applications, files, credentials, and external systems. Use when you need to know what a bot depends on, what a shared sub-bot is used by, or to support change-impact analysis and troubleshooting. Uses a360tools deps and records the graph for reuse.
---

# 11 · Dependency analysis

**Goal:** know what a bot depends on and what depends on it.

Build the chain:

```
BOT → SUB-BOT → ACTION → PACKAGE → VARIABLE → APPLICATION → FILE
→ CREDENTIAL → EXTERNAL SYSTEM
```

## When to use

- Before changing a shared component (`09`, `15`).
- During troubleshooting (`07`) to find the external factor.
- When documenting (`10`) or inventorying (`03`).

## Method

```bash
cd "${CLAUDE_PLUGIN_ROOT}/scripts" 2>/dev/null || cd tools   # installed plugin, else this repo
python -m a360tools deps <bot_file>            # edges for one bot
python -m a360tools inventory <corpus> --json  # cross-bot package/usage view
```

Extract and record:

- **Outbound:** packages (name+version), sub-bots ("Run task" targets), files &
  folders, credentials (Vault references), applications, external systems.
- **Inbound (reverse):** which bots call this bot / sub-bot (search the corpus).

## Output

- A dependency list/graph for the bot (and, where relevant, the reverse
  "used-by" set).
- Note version-sensitive package dependencies (they matter for portability and
  `15-change-impact-analysis`).
- Save notable graphs under `knowledge/bots/`.

## Guardrail

Dependency extraction is only as good as the confirmed schema. Where a
dependency type (e.g. how a credential reference is stored) is still `INFERRED`,
say the graph may be incomplete for that type.
