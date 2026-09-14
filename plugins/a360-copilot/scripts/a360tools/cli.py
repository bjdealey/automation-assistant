"""Command-line interface for a360tools.

    python -m a360tools <command> [args]

Commands print a concise human summary by default; add ``--json`` for the full
machine-readable result. ``normalize`` always emits JSON (that is its purpose).
"""

from __future__ import annotations

import argparse
import json
import sys

from . import (complexity, crawl, dependencies, diff, extract, ingest,
               inventory, model, validate)


def _emit(obj, as_json: bool, renderer) -> None:
    if as_json:
        print(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        renderer(obj)


def _load(path: str):
    try:
        return model.load_bot(path)
    except model.BotLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)


# --------------------------------- renderers ---------------------------------

def _r_crawl(rows):
    print(f"{len(rows)} candidate bot file(s):")
    for r in rows:
        size = "?" if r["size"] is None else f"{r['size']}B"
        print(f"  {r['relpath']}  ({size})")


def _r_inventory(inv):
    agg = inv["aggregate"]
    print(f"root: {inv['root']}")
    print(f"bots: {agg['bot_count']}   errors: {agg['error_count']}")
    print("\ntop packages (bots using):")
    for p in agg["packages_by_frequency"][:10]:
        print(f"  {p['bots_using']:>4}  {p['name']}")
    print("\ntop actions (total uses):")
    for a in agg["top_actions"][:10]:
        print(f"  {a['total_uses']:>4}  {a['package']} :: {a['command']}")
    print("\nper-bot:")
    for b in inv["bots"]:
        print(f"  [{b['complexity_score']:>4}] {b['relpath']}  "
              f"(actions={b['action_count']} vars={b['variable_count']} "
              f"loops={b['loops']} pkgs={b['package_count']})")
    for e in inv["errors"]:
        print(f"  !! {e['path']}: {e['error']}")


def _r_extract(x):
    print(f"packages ({len(x['packages'])}):")
    for p in x["packages"]:
        print(f"  {p['name']}  {p['version'] or '(no version)'}")
    print(f"\nactions ({x['action_count']} total):")
    for a in x["actions"]:
        print(f"  {a['count']:>3}  {a['package']} :: {a['command']}")
    print(f"\nvariables ({len(x['variables'])}):")
    for v in x["variables"]:
        io = "".join(["I" if v["input"] else "", "O" if v["output"] else ""]) or "-"
        print(f"  [{io}] {v['name']}: {v['type'] or '?'}")
    if "note" in x:
        print(f"\nnote: {x['note']}")


def _r_deps(d):
    for key in ("packages", "sub_bots", "files", "urls", "credentials"):
        items = d[key]
        print(f"{key} ({len(items)}):")
        for it in items:
            if key == "packages":
                print(f"  {it['name']} {it['version'] or ''}".rstrip())
            else:
                ref = it.get("reference", "")
                print(f"  {ref}  @ {it.get('at', '')}")
    print(f"\nmethod: {d['_method']}")


def _r_complexity(m):
    for k, v in m.items():
        if k.startswith("_"):
            continue  # meta keys (e.g. _note) are rendered separately
        print(f"  {k:>18}: {v}")
    print(f"\nnote: {m['_note']}")


def _r_diff(d):
    if not d["changed"]:
        print("no structural differences detected")
        return
    pk = d["packages"]
    print(f"packages: +{pk['added']} -{pk['removed']} "
          f"~{[c['name'] for c in pk['version_changed']]}")
    vr = d["variables"]
    print(f"variables: +{vr['added']} -{vr['removed']} "
          f"~{[c['name'] for c in vr['type_changed']]}")
    print(f"actions: total {d['actions']['total_old']} -> {d['actions']['total_new']}")
    for a in d["actions"]["usage_changed"]:
        sign = "+" if a["delta"] > 0 else ""
        print(f"  {sign}{a['delta']}  {a['package']} :: {a['command']}")


def _r_ingest_plan(p):
    print(f"bot: {p['name'] or '(unnamed)'}   version: {p['version'] or '?'}")
    print(f"hash: {p['hash']}")
    print(f"provenance: {p['provenance']}   idempotent_noop: {p['idempotent_noop']}")
    if p["idempotent_noop"]:
        print("already ingested (hash in ledger); nothing to propose.")
        return
    print(f"\nproposed entries ({len(p['entries'])}):")
    for e in p["entries"]:
        print(f"  [{e['confidence']:<9}] {e['target']}/{e['kind']}: {e['statement']}")


def _r_ingest_corpus(c):
    plans = c["plans"]
    noop = sum(1 for p in plans if p["idempotent_noop"])
    print(f"root: {c['root']}")
    print(f"bots: {len(plans)}   new: {len(plans) - noop}   "
          f"already-ingested: {noop}   errors: {len(c['errors'])}")
    for p in plans:
        tag = "already ingested" if p["idempotent_noop"] else f"{len(p['entries'])} entries"
        print(f"  {(p['name'] or '(unnamed)'):<24} {p['hash'][:12]}  {tag}")
    for e in c["errors"]:
        print(f"  ERROR {e['path']}: {e['error']}")


def _r_validate(rep):
    s = rep["summary"]
    print(f"json_parse: {rep['json_parse']}   recognised: {rep['recognised']}")
    print("summary: " + "  ".join(f"{k}={s[k]}" for k in validate.SEVERITY_RANK))
    for f in rep["findings"]:
        print(f"  {f['severity']:<8} [{f['check']}] {f['location']}\n"
              f"           {f['message']} (confidence: {f['confidence']})")
    print(f"\n{rep['_disclaimer']}")


# ---------------------------------- main ----------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="a360tools", description=__doc__)
    p.add_argument("--json", action="store_true", help="emit full JSON output")
    sub = p.add_subparsers(dest="command", required=True)

    # --json is accepted before OR after the subcommand. The per-subcommand copy
    # uses a SUPPRESS default so it never clobbers a --json given before it.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                        help="emit full JSON output (may also precede the subcommand)")

    sp = sub.add_parser("crawl", parents=[common],
                        help="find candidate bot files in a folder")
    sp.add_argument("path")

    sp = sub.add_parser("inventory", parents=[common],
                        help="summarise a corpus of bots")
    sp.add_argument("path")

    for name, help_ in (("extract", "packages/actions/variables of one bot"),
                        ("deps", "dependency edges of one bot"),
                        ("complexity", "complexity metrics of one bot"),
                        ("validate", "heuristic validation report of one bot")):
        sp = sub.add_parser(name, parents=[common], help=help_)
        sp.add_argument("file")

    sp = sub.add_parser("diff", parents=[common], help="structural diff of two bots")
    sp.add_argument("old")
    sp.add_argument("new")

    sp = sub.add_parser("normalize", parents=[common],
                        help="stable, sorted JSON (validated round-trip)")
    sp.add_argument("file")
    sp.add_argument("-o", "--output", help="write to file instead of stdout")

    sp = sub.add_parser("ingest-plan", parents=[common],
                        help="propose knowledge/ entries for one bot (read-only)")
    sp.add_argument("file")
    sp.add_argument("--attested-export", action="store_true",
                    help="attest this is a genuine Control Room export (allows CONFIRMED)")
    sp.add_argument("--ledger",
                    help="ingest ledger JSON; an already-recorded bot is a no-op")

    sp = sub.add_parser("ingest-corpus", parents=[common],
                        help="propose knowledge/ entries for a folder of bots (read-only)")
    sp.add_argument("path")
    sp.add_argument("--attested-export", action="store_true",
                    help="attest these are genuine Control Room exports (allows CONFIRMED)")
    sp.add_argument("--ledger",
                    help="ingest ledger JSON; already-recorded bots are skipped")

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    as_json = args.json

    if args.command == "crawl":
        _emit(crawl.find_bot_files(args.path), as_json, _r_crawl)
    elif args.command == "inventory":
        _emit(inventory.inventory(args.path), as_json, _r_inventory)
    elif args.command == "extract":
        _emit(extract.extract_all(_load(args.file)), as_json, _r_extract)
    elif args.command == "deps":
        _emit(dependencies.extract_dependencies(_load(args.file)), as_json, _r_deps)
    elif args.command == "complexity":
        _emit(complexity.metrics(_load(args.file)), as_json, _r_complexity)
    elif args.command == "validate":
        _emit(validate.validate_bot(_load(args.file)), as_json, _r_validate)
    elif args.command == "diff":
        _emit(diff.diff_bots(_load(args.old), _load(args.new)), as_json, _r_diff)
    elif args.command == "ingest-plan":
        ledger = ingest.load_ledger(args.ledger) if args.ledger else None
        plan = ingest.plan(_load(args.file), attested=args.attested_export,
                           ledger=ledger, source=args.file)
        _emit(plan, as_json, _r_ingest_plan)
    elif args.command == "ingest-corpus":
        ledger = ingest.load_ledger(args.ledger) if args.ledger else None
        result = ingest.plan_corpus(args.path, attested=args.attested_export,
                                    ledger=ledger)
        _emit(result, as_json, _r_ingest_corpus)
    elif args.command == "normalize":
        data = _load(args.file)
        text = model.normalized_json(data)
        # round-trip validation: the normalised text must parse back equal.
        if json.loads(text) != data:  # pragma: no cover - defensive
            print("error: normalisation changed the data", file=sys.stderr)
            return 2
        if args.output:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
            print(f"wrote {args.output}")
        else:
            print(text)
    return 0
