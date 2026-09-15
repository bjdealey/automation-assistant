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


# ------------------------------- model / Bot -------------------------------

def test_classify_command_categories():
    cc = model.classify_command
    assert cc("Loop", "Loop") == "loop"
    assert cc(None, "forEach") == "loop"
    assert cc(None, "while") == "loop"
    assert cc("TaskBot", "runTask") == "runtask"
    assert cc(None, "runBot") == "runtask"
    assert cc("TryCatch", "try") == "error"       # untested branch before now
    assert cc(None, "finally") == "error"
    assert cc("IF", "if") == "conditional"
    assert cc(None, "elseIf") == "conditional"
    assert cc("Delay", "delay") == "wait"
    assert cc(None, "sleep") == "wait"
    assert cc("Excel", "Open") == "other"         # untested branch before now
    assert cc(None, None) == "other"


def test_bot_tolerant_of_unknown_shape():
    b = model.Bot.of({"totally": "unrelated"})     # must not raise
    assert b.packages == [] and b.variables == [] and b.actions == []
    assert b.action_usage == [] and b.action_nodes == []
    assert b.string_leaves                          # the one string leaf is found
    assert b.depth >= 1


def test_bot_does_not_mutate_input(bot):
    before = copy.deepcopy(bot)
    b = model.Bot.of(bot)
    _ = (b.packages, b.variables, b.actions, b.action_usage,
         b.string_leaves, b.dicts, b.action_nodes, b.depth, b.variable_names)
    assert bot == before


def test_validate_flags_posix_absolute_path():
    # Regression lock on the drifted _ABS_PATH_RE: validate must flag POSIX paths
    # (its old regex only matched Windows/UNC, so /mnt/... slipped through).
    bot = {"nodes": [{"packageName": "X", "commandName": "y",
                      "attributes": [{"name": "path", "value": "/mnt/data/in.csv"}]}]}
    findings = validate.validate_bot(bot)["findings"]
    assert any(f["check"] == "hardcoded_path" for f in findings)


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


def test_var_ref_names_handles_real_token_forms():
    # CONFIRMED forms from a real export: plain, type-method, record-field, global.
    assert model.var_ref_names("$strBatch$") == ["strBatch"]
    assert model.var_ref_names("$strTaskName.String:trim$") == ["strTaskName"]
    assert model.var_ref_names("$recRunConfig{sEnv}$") == ["recRunConfig"]
    assert model.var_ref_names("$a$-$b.String:upper$") == ["a", "b"]
    # globals excluded by default, included on request
    assert model.var_ref_names("$@Temp_Files$") == []
    assert model.var_ref_names("$@Temp_Files$", include_globals=True) == ["Temp_Files"]
    # a bare dollar amount is not a reference
    assert model.var_ref_names("$5.00 due") == []
    # namespace/system reference ($System:member$) is not a declared bot var
    assert model.var_ref_names("[WARNING] $System:AATaskName$ missing") == []
    # embedded VBScript/PowerShell must not be mined for references: two $ across
    # code separated by whitespace/operators do NOT form a token
    assert model.var_ref_names('cmd = "$env:TEMP"\n  If $_ -gt 5 Then $cpu = 1') == []


def test_validate_global_reference_not_flagged_undefined():
    # A global-value reference ($@Global$) must not be reported as an undefined
    # bot variable — globals are Control Room state, not declared here.
    bot = {"nodes": [{"packageName": "File", "commandName": "copy",
                      "attributes": [{"name": "src", "value": {
                          "type": "STRING", "expression": "$@RPA_Directory$/x.csv"}}]}],
           "variables": [], "packages": []}
    rep = validate.validate_bot(bot)
    assert not [f for f in rep["findings"] if f["check"] == "undefined_variable"]


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


def test_diff_package_version_change():
    old = {"packages": [{"name": "Excel", "version": "3.2.0"}]}
    new = {"packages": [{"name": "Excel", "version": "4.0.0"}]}
    vc = diff.diff_bots(old, new)["packages"]["version_changed"]
    assert len(vc) == 1 and vc[0]["name"] == "Excel"
    assert vc[0]["old"] == ["3.2.0"] and vc[0]["new"] == ["4.0.0"]


def test_diff_package_multiversion_not_collapsed():
    # one name at two versions in a single bot must not collapse to the last one
    old = {"packages": [{"name": "Excel", "version": "3.2.0"},
                        {"name": "Excel", "version": "4.0.0"}]}
    new = {"packages": [{"name": "Excel", "version": "3.2.0"}]}
    vc = diff.diff_bots(old, new)["packages"]["version_changed"]
    assert len(vc) == 1
    assert vc[0]["old"] == ["3.2.0", "4.0.0"]   # both versions preserved
    assert vc[0]["new"] == ["3.2.0"]


# -------------------------------- crawl/inv --------------------------------

def test_crawl_finds_fixture():
    rows = crawl.find_bot_files(FIXTURES)
    rels = {r["relpath"] for r in rows}
    assert "hypothesis_bot.json" in rels
    assert "_invalid.bot" in rels


def test_crawl_finds_extensionless_taskbot_and_skips_manifest(tmp_path):
    # Real Control Room exports store taskbots as EXTENSIONLESS files beside a
    # manifest.json that is not a bot. Discovery must find the bot by content
    # and drop the manifest (the exact ground-truth failure this replaces).
    (tmp_path / "Some Bot").write_text(  # no extension, real export layout
        json.dumps({"nodes": [], "variables": [], "packages": []}))
    (tmp_path / "manifest.json").write_text(
        json.dumps({"files": [], "packages": [], "globalValues": []}))
    (tmp_path / "preview.png").write_bytes(b"\x89PNG not json")

    rels = {r["relpath"] for r in crawl.find_bot_files(str(tmp_path))}
    assert rels == {"Some Bot"}


def test_crawl_load_bot_files_splits_loaded_and_errors():
    loaded, errors = crawl.load_bot_files(FIXTURES)
    rels = {f["relpath"] for f, _ in loaded}
    assert {"hypothesis_bot.json", "real_botcode7.bot"} <= rels  # good bots load
    assert all(isinstance(data, dict) for _, data in loaded)
    assert len(errors) == 1 and errors[0]["path"].endswith("_invalid.bot")


def test_inventory_handles_good_and_bad():
    inv = inventory.inventory(FIXTURES)
    assert inv["aggregate"]["bot_count"] >= 1
    assert inv["aggregate"]["error_count"] >= 1   # _invalid.bot
    assert any(b["relpath"] == "hypothesis_bot.json" for b in inv["bots"])


# --------------------------- real export shape ---------------------------
# real_botcode7.bot reproduces CONFIRMED structures from a real Control Room
# export (botCodeVersion 7): TASKBOT taskbotFile refs, returnTo, input/output
# variables, real package versions, and the $var$/$var.T:m$/$rec{f}$/$@g$/
# $System:m$ reference forms. Content is synthetic (no secrets/PII); the SHAPE
# is real. These assertions pin the extractors to that shape.

REAL = os.path.join(FIXTURES, "real_botcode7.bot")


@pytest.fixture
def real_bot():
    return model.load_bot(REAL)


def test_real_bot_loads_and_is_recognised_as_bot():
    d = model.load_bot(REAL)
    assert model.looks_like_bot(d)
    assert d["properties"]["botCodeVersion"] == "7"


def test_real_bot_packages_and_io_variables(real_bot):
    b = model.Bot.of(real_bot)
    pkgs = {p["name"]: p["version"] for p in b.packages}
    assert pkgs["TaskBot"] == "2.10.0-20241119-100739"
    assert pkgs["ErrorHandler"] == "2.13.0-20241115-120032"
    v = {x["name"]: x for x in b.variables}
    assert v["strTaskName"]["input"] is True and v["strTaskName"]["output"] is False
    assert v["strResult"]["output"] is True


def test_real_bot_actions_include_runtask(real_bot):
    pairs = {(a["package"], a["command"]) for a in model.Bot.of(real_bot).actions}
    assert ("TaskBot", "runTask") in pairs
    assert ("String", "replace") in pairs


def test_real_bot_sub_bot_reference_decoded(real_bot):
    refs = [s["reference"] for s in dependencies.extract_dependencies(real_bot)["sub_bots"]]
    assert refs == ["repository:///Automation Anywhere/Bots/Demo/Child Bots/Sub Worker"]


def test_real_bot_validate_has_no_false_undefined_vars(real_bot):
    # method / record / global / namespace reference forms must all resolve; the
    # only declared-but-referenced vars are strTaskName, strBatch, strResult.
    rep = validate.validate_bot(real_bot)
    assert rep["recognised"] is True
    assert not [f for f in rep["findings"] if f["check"] == "undefined_variable"]


def test_real_bot_complexity_counts_runtask_and_error_handlers(real_bot):
    m = complexity.metrics(real_bot)
    assert m["sub_bot_calls"] == 1
    assert m["error_handlers"] == 3   # try + catch + finally


# ---------------------------------- cli ----------------------------------

def test_cli_extract_json(capsys):
    rc = cli.main(["--json", "extract", SAMPLE])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["action_count"] == 7


def test_cli_json_after_subcommand(capsys):
    # --json is accepted AFTER the subcommand too, not only before it.
    rc = cli.main(["extract", SAMPLE, "--json"])
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


def test_cli_renderers_run_in_text_mode(capsys):
    # Exercise every human renderer (no --json) so a KeyError/crash inside a
    # renderer surfaces here instead of only in production.
    for argv in (
        ["crawl", FIXTURES],
        ["inventory", FIXTURES],
        ["extract", SAMPLE],
        ["deps", SAMPLE],
        ["complexity", SAMPLE],
        ["diff", SAMPLE, SAMPLE],
        ["ingest-plan", SAMPLE],
        ["ingest-corpus", FIXTURES],
    ):
        rc = cli.main(argv)
        assert rc == 0, argv
        assert capsys.readouterr().out.strip(), argv


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
