"""Tests for a360tools against the synthetic fixture.

The fixture reflects the *hypothesised* A360 schema (see
knowledge/schema/a360-bot-json.md). When the real schema is confirmed, update
both the fixture and these assertions together.
"""

import copy
import json
import os

import pytest

from a360tools import (complexity, crawl, dependencies, diff, extract,
                       ingest, inventory, model, validate)
from a360tools import cli

HERE = os.path.dirname(__file__)
FIXTURES = os.path.join(HERE, "fixtures")
SAMPLE = os.path.join(FIXTURES, "hypothesis_bot.json")


@pytest.fixture
def bot():
    return model.load_bot(SAMPLE)


# --------------------------------- loading ---------------------------------

def test_load_missing_file():
    with pytest.raises(model.BotLoadError):
        model.load_bot(os.path.join(FIXTURES, "does_not_exist.json"))


def test_load_invalid_json():
    with pytest.raises(model.BotLoadError):
        model.load_bot(os.path.join(FIXTURES, "_invalid.bot"))


# --------------------------------- extract ---------------------------------

def test_extract_packages(bot):
    names = [p["name"] for p in extract.extract_packages(bot)]
    assert names == ["Excel", "Loop", "String"]  # sorted
    excel = next(p for p in extract.extract_packages(bot) if p["name"] == "Excel")
    assert excel["version"] == "3.2.0"


def test_extract_variables(bot):
    vs = {v["name"]: v for v in extract.extract_variables(bot)}
    assert set(vs) == {"vInvoiceFolder", "vCount", "vApiPassword"}
    assert vs["vInvoiceFolder"]["input"] is True
    assert vs["vApiPassword"]["type"] == "CREDENTIAL"


def test_extract_actions_count_and_categories(bot):
    actions = extract.extract_actions(bot)
    assert len(actions) == 7
    cats = {(a["package"], a["command"]): a["category"] for a in actions}
    assert cats[("Loop", "Loop")] == "loop"
    assert cats[("IF", "if")] == "conditional"
    assert cats[("TaskBot", "runTask")] == "runtask"
    assert cats[("Delay", "delay")] == "wait"


def test_extract_all_note_when_unrecognised():
    result = extract.extract_all({"totally": "unrelated"})
    assert "note" in result
    assert result["action_count"] == 0


# ------------------------------ dependencies ------------------------------

def test_dependencies(bot):
    deps = dependencies.extract_dependencies(bot)
    assert [p["name"] for p in deps["packages"]] == ["Excel", "Loop", "String"]
    assert any(s["reference"] == "Bots/ProcessInvoice.bot" for s in deps["sub_bots"])
    assert any(f["reference"] == "C:\\data\\invoices.xlsx" for f in deps["files"])
    assert any("api.example.com" in u["reference"] for u in deps["urls"])
    assert any(c["reference"] == "vApiPassword" for c in deps["credentials"])


# ------------------------------- complexity -------------------------------

def test_complexity_metrics(bot):
    m = complexity.metrics(bot)
    assert m["action_count"] == 7
    assert m["loops"] == 1
    assert m["conditionals"] == 1
    assert m["sub_bot_calls"] == 1
    assert m["fixed_waits"] == 1
    assert m["variable_count"] == 3
    assert m["distinct_packages"] == 3
    assert m["complexity_score"] == 15


# -------------------------------- validate --------------------------------

def test_validate_findings(bot):
    rep = validate.validate_bot(bot)
    checks = [f["check"] for f in rep["findings"]]
    assert "hardcoded_secret" in checks          # the literal password attribute
    assert "undefined_variable" in checks         # $vMissing$
    assert "hardcoded_path" in checks             # C:\data\invoices.xlsx
    assert "fixed_wait" in checks                 # the delay action
    assert rep["recognised"] is True
    assert rep["summary"]["HIGH"] >= 1


def test_validate_never_leaks_secret_value(bot):
    rep = validate.validate_bot(bot)
    assert "hunter2SuperSecret" not in json.dumps(rep)


def test_validate_undefined_variable_is_vmissing(bot):
    rep = validate.validate_bot(bot)
    undefined = [f for f in rep["findings"] if f["check"] == "undefined_variable"]
    assert any("vMissing" in f["message"] for f in undefined)


# ---------------------------------- diff ----------------------------------

def test_diff_detects_changes(bot):
    new = copy.deepcopy(bot)
    new["packages"].append({"name": "Database", "version": "1.0.0"})
    new["variables"][1]["type"] = "STRING"      # vCount NUMBER -> STRING
    new["nodes"].pop()                            # remove the Rest node (n7)

    d = diff.diff_bots(bot, new)
    assert d["changed"] is True
    assert "Database" in d["packages"]["added"]
    assert any(c["name"] == "vCount" for c in d["variables"]["type_changed"])
    assert d["actions"]["total_new"] < d["actions"]["total_old"]


def test_diff_identical_is_no_change(bot):
    assert diff.diff_bots(bot, copy.deepcopy(bot))["changed"] is False


# -------------------------------- crawl/inv --------------------------------

def test_crawl_finds_fixture():
    rows = crawl.find_bot_files(FIXTURES)
    rels = {r["relpath"] for r in rows}
    assert "hypothesis_bot.json" in rels
    assert "_invalid.bot" in rels


def test_inventory_handles_good_and_bad():
    inv = inventory.inventory(FIXTURES)
    assert inv["aggregate"]["bot_count"] >= 1
    assert inv["aggregate"]["error_count"] >= 1   # _invalid.bot
    assert any(b["relpath"] == "hypothesis_bot.json" for b in inv["bots"])


# ---------------------------------- cli ----------------------------------

def test_cli_extract_json(capsys):
    rc = cli.main(["--json", "extract", SAMPLE])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["action_count"] == 7


def test_cli_validate_text_runs(capsys):
    rc = cli.main(["validate", SAMPLE])
    assert rc == 0
    assert "summary:" in capsys.readouterr().out


def test_cli_normalize_roundtrips(capsys, bot):
    rc = cli.main(["normalize", SAMPLE])
    assert rc == 0
    assert json.loads(capsys.readouterr().out) == bot


def test_cli_bad_file_exits_2():
    with pytest.raises(SystemExit) as exc:
        cli.main(["extract", os.path.join(FIXTURES, "_invalid.bot")])
    assert exc.value.code == 2


# --------------------------------- ingest ---------------------------------

def test_ingest_hash_stable_across_formatting(bot):
    h1 = ingest.bot_hash(bot)
    reordered = {k: bot[k] for k in reversed(list(bot.keys()))}  # same data, new order
    h2 = ingest.bot_hash(reordered)
    assert h1 == h2
    assert len(h1) == 64  # sha256 hex digest


def test_ingest_identity(bot):
    p = ingest.plan(bot)
    assert p["name"] == "SampleInvoiceBot"
    assert p["version"] == "2"          # metadata.schemaVersion
    assert p["hash"] == ingest.bot_hash(bot)


def test_ingest_default_all_observed(bot):
    p = ingest.plan(bot)
    assert p["provenance"] == "observed"
    assert p["entries"]
    assert all(e["confidence"] == "OBSERVED" for e in p["entries"])


def test_ingest_attested_confirms_only_structural(bot):
    p = ingest.plan(bot, attested=True)
    assert p["provenance"] == "attested-export"
    structural = [e for e in p["entries"] if e["structural"]]
    observational = [e for e in p["entries"] if not e["structural"]]
    assert structural and observational   # the fixture yields both kinds
    assert all(e["confidence"] == "CONFIRMED" for e in structural)
    assert all(e["confidence"] == "OBSERVED" for e in observational)


def test_ingest_entries_carry_version_and_hash_evidence(bot):
    p = ingest.plan(bot)
    for e in p["entries"]:
        assert e["version"] == "2"
        assert p["hash"] in e["evidence"]


def test_ingest_proposes_package_variable_action_facts(bot):
    statements = [e["statement"] for e in ingest.plan(bot)["entries"]]
    assert any("Excel" in s and "3.2.0" in s for s in statements)
    assert any("Excel.Open" in s for s in statements)
    assert any("CREDENTIAL" in s for s in statements)


def test_ingest_never_leaks_secret_value(bot):
    p = ingest.plan(bot, attested=True)
    assert "hunter2SuperSecret" not in json.dumps(p)


def test_ingest_ledger_line_shape(bot):
    p = ingest.plan(bot, source="corpus/sample.json")
    line = p["ledger_line"]
    assert line["hash"] == p["hash"]
    assert line["name"] == "SampleInvoiceBot"
    assert line["version"] == "2"
    assert line["provenance"] == "observed"
    assert line["source"] == "corpus/sample.json"


def test_ingest_plan_is_read_only(bot):
    before = copy.deepcopy(bot)
    ingest.plan(bot, attested=True)
    assert bot == before


def test_ingest_noop_when_hash_in_ledger(bot):
    h = ingest.bot_hash(bot)
    ledger = {h: {"name": "SampleInvoiceBot", "version": "2",
                  "provenance": "observed", "first_seen": "2026-01-01",
                  "source": "corpus/x.json"}}
    p = ingest.plan(bot, ledger=ledger)
    assert p["idempotent_noop"] is True
    assert p["entries"] == []
    assert p["ledger_line"] is None
    assert p["hash"] == h          # identity still reported for display


def test_ingest_new_bot_emits_one_ledger_line(bot):
    # a ledger that does NOT contain this bot's hash -> not a no-op
    p = ingest.plan(bot, ledger={"0" * 64: {}}, source="corpus/x.json")
    assert p["idempotent_noop"] is False
    assert p["entries"]
    assert p["ledger_line"]["hash"] == p["hash"]
    assert p["ledger_line"]["source"] == "corpus/x.json"


def test_ingest_empty_ledger_is_not_noop(bot):
    p = ingest.plan(bot, ledger={})
    assert p["idempotent_noop"] is False
    assert p["entries"]


def test_load_ledger_missing_returns_empty(tmp_path):
    assert ingest.load_ledger(str(tmp_path / "nope.json")) == {}


def test_ingest_corpus_one_plan_per_bot_skips_ledgered(tmp_path, bot):
    (tmp_path / "a.json").write_text(json.dumps(bot))               # hash in ledger
    (tmp_path / "b.json").write_text(json.dumps({**bot, "_variant": 1}))  # new bot
    ledger = {ingest.bot_hash(bot): {"name": "x", "version": "2",
              "provenance": "observed", "first_seen": "2026-01-01", "source": "a"}}
    result = ingest.plan_corpus(str(tmp_path), ledger=ledger)
    assert len(result["plans"]) == 2                    # one plan per discovered bot
    noop = [p for p in result["plans"] if p["idempotent_noop"]]
    new = [p for p in result["plans"] if not p["idempotent_noop"]]
    assert len(noop) == 1 and noop[0]["entries"] == []  # ledgered bot proposes nothing
    assert len(new) == 1 and new[0]["entries"]          # new bot proposes entries


def test_ingest_corpus_dedups_identical_bots_within_run(tmp_path, bot):
    (tmp_path / "a.json").write_text(json.dumps(bot))
    (tmp_path / "copy.json").write_text(json.dumps(bot))   # same content, same hash
    result = ingest.plan_corpus(str(tmp_path))             # empty ledger
    assert len(result["plans"]) == 2
    noops = [p for p in result["plans"] if p["idempotent_noop"]]
    assert len(noops) == 1                                 # 2nd identical file is a no-op


def test_ingest_corpus_collects_load_errors(tmp_path, bot):
    (tmp_path / "ok.json").write_text(json.dumps(bot))
    (tmp_path / "bad.bot").write_text("{not json")
    result = ingest.plan_corpus(str(tmp_path))
    assert len(result["plans"]) == 1
    assert len(result["errors"]) == 1


def test_ingest_corpus_does_not_mutate_caller_ledger(tmp_path, bot):
    (tmp_path / "a.json").write_text(json.dumps(bot))
    ledger: dict = {}
    ingest.plan_corpus(str(tmp_path), ledger=ledger)
    assert ledger == {}                                    # caller's ledger untouched


def test_cli_ingest_corpus_json(tmp_path, bot, capsys):
    (tmp_path / "a.json").write_text(json.dumps(bot))
    rc = cli.main(["--json", "ingest-corpus", str(tmp_path)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert len(out["plans"]) == 1
    assert out["plans"][0]["entries"]


def test_cli_ingest_plan_json(capsys):
    rc = cli.main(["--json", "ingest-plan", SAMPLE])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["name"] == "SampleInvoiceBot"
    assert out["entries"]


def test_cli_ingest_plan_attested_flag(capsys):
    rc = cli.main(["--json", "ingest-plan", SAMPLE, "--attested-export"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["provenance"] == "attested-export"
    assert any(e["confidence"] == "CONFIRMED" for e in out["entries"])
