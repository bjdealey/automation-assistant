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
                       inventory, model, validate)
from a360tools import cli

HERE = os.path.dirname(__file__)
FIXTURES = os.path.join(HERE, "fixtures")
SAMPLE = os.path.join(FIXTURES, "sample_bot.json")


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
    assert "sample_bot.json" in rels
    assert "_invalid.bot" in rels


def test_inventory_handles_good_and_bad():
    inv = inventory.inventory(FIXTURES)
    assert inv["aggregate"]["bot_count"] >= 1
    assert inv["aggregate"]["error_count"] >= 1   # _invalid.bot
    assert any(b["relpath"] == "sample_bot.json" for b in inv["bots"])


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
