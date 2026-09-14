# a360tools

Deterministic, **read-only** utilities for analysing Automation Anywhere A360
bot JSON, plus a JSON normaliser. Standard library only — no dependencies.

> **Schema-tolerant by design.** The exact A360 bot schema is not yet
> `CONFIRMED` (see `../knowledge/schema/a360-bot-json.md`), so these tools
> *discover* structure by walking the JSON and matching a small set of candidate
> key names. They never crash on an unrecognised shape — they return empty
> results and say so. As the schema is validated, tighten the matchers in
> `a360tools/model.py` and extend the tests.

## Commands

```bash
python -m a360tools crawl      <dir>              # list candidate .bot/.json files
python -m a360tools inventory  <dir>              # per-bot + aggregate corpus summary
python -m a360tools extract    <bot_file>         # packages / actions / variables
python -m a360tools deps       <bot_file>         # dependency edges
python -m a360tools complexity <bot_file>         # structural complexity metrics
python -m a360tools validate   <bot_file>         # heuristic validation/hygiene report
python -m a360tools diff       <old> <new>        # structural diff (packages/vars/actions)
python -m a360tools normalize  <bot_file> [-o f]  # stable sorted JSON (round-trip checked)
```

Add `--json` (before or after the subcommand) for full machine-readable output, e.g.:

```bash
python -m a360tools --json inventory ../knowledge/bots/corpus
```

## Design guarantees

- **Read-only:** analysis never mutates inputs. `normalize` is the only
  transformer; it validates the round-trip (`parse → dump → parse == original`)
  before writing, per the repo rule
  `INPUT → VALIDATION → TRANSFORMATION → VALIDATION → OUTPUT`.
- **Deterministic:** outputs are sorted; the same input yields the same output.
- **Honest:** heuristic results are labelled (`_method`, `_note`, `_disclaimer`);
  the validation report is a *signal*, not a control-room validity verdict.
- **Safe with secrets:** the validator reports a secret's *location and kind*,
  never its value.

## Layout

```
tools/
├── pyproject.toml
├── conftest.py            # makes a360tools importable under pytest
├── a360tools/
│   ├── model.py           # schema-tolerant loading + traversal + predicates
│   ├── extract.py         # packages / actions / variables
│   ├── crawl.py           # find bot files
│   ├── inventory.py       # corpus inventory
│   ├── dependencies.py    # dependency edges
│   ├── complexity.py      # metrics
│   ├── diff.py            # structural diff
│   ├── validate.py        # heuristic validation report
│   └── cli.py             # argparse CLI + renderers
└── tests/
    ├── fixtures/hypothesis_bot.json  # synthetic bot encoding the schema HYPOTHESIS (not truth)
    └── test_a360tools.py
```

## Tests

```bash
cd tools
python -m pytest -q
```

The fixture reflects the **hypothesised** schema. When you confirm the real
schema from an export, update the fixture and the assertions together so code
and knowledge stay in sync.
