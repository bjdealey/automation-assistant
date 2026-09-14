"""Turn one bot into a deterministic ingest *plan* (read-only).

An ingest plan is what the learning loop proposes to add to ``knowledge/`` from
a single bot: source-tagged entries, a stable identity hash, and one ledger
line. It mutates nothing — the agent (skill 03) is what applies the plan to the
working tree, and git is the commit gate.

Confidence follows the provenance rule in
``docs/adr/0001-ingest-confirms-only-attested-exports.md``: entries are OBSERVED
by default; only when the engineer attests the bot is a genuine Control Room
export (``attested=True``) may the *structural* facts it directly evidences be
CONFIRMED. Observational facts stay OBSERVED regardless.

Schema-tolerant, like the rest of the package: it discovers what it can and
never raises on an unfamiliar document.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from . import extract, model

METADATA_KEYS = ("metadata", "meta")
SCHEMA_VERSION_KEYS = ("schemaversion", "version")


def bot_hash(bot: Any) -> str:
    """Stable sha256 hex digest of the bot's normalised JSON (its identity)."""
    return hashlib.sha256(model.normalized_json(bot).encode("utf-8")).hexdigest()


def _identity(bot: Any) -> tuple[str | None, str | None]:
    """(name, A360/schema version), tolerating a top-level or metadata home."""
    meta = model.get_ci(bot, *METADATA_KEYS)
    meta = meta if isinstance(meta, dict) else {}
    name = model.get_ci(meta, *model.NAME_KEYS)
    if not isinstance(name, str):
        name = model.get_ci(bot, *model.NAME_KEYS)
    version = model.get_ci(meta, *SCHEMA_VERSION_KEYS)
    if not isinstance(version, str):
        version = model.get_ci(bot, *SCHEMA_VERSION_KEYS)
    return (name if isinstance(name, str) else None,
            version if isinstance(version, str) else None)


def _entry(target, kind, statement, structural, version, evidence, attested) -> dict:
    return {
        "target": target,
        "kind": kind,
        "statement": statement,
        "structural": structural,
        # ADR-0001: CONFIRMED only for structural facts of an attested export.
        "confidence": "CONFIRMED" if (attested and structural) else "OBSERVED",
        "version": version,
        "evidence": evidence,
    }


def _entries(bot: Any, version: str | None, h: str, attested: bool) -> list[dict]:
    """Proposed knowledge entries. Cites only structure — never attribute values,
    so secrets in the bot are never echoed into a proposed entry."""
    ev = f"bot {h}"
    entries: list[dict] = []

    # --- Structural facts: what the JSON schema looks like (CONFIRMABLE) ---
    if isinstance(bot, dict):
        keys = ", ".join(sorted(str(k) for k in bot.keys()))
        entries.append(_entry(
            "schema", "envelope",
            f"Bot envelope has top-level keys: {keys}.",
            True, version, ev, attested))

    packages = extract.extract_packages(bot)
    for p in packages:
        at = f" at version {p['version']}" if p["version"] else ""
        entries.append(_entry(
            "schema", "package",
            f"Package `{p['name']}` present{at}.",
            True, version, ev, attested))

    var_types = sorted({v["type"] for v in extract.extract_variables(bot) if v["type"]})
    for t in var_types:
        entries.append(_entry(
            "schema", "variable-type",
            f"Variable type `{t}` present.",
            True, version, ev, attested))

    actions = sorted({(a["package"], a["command"]) for a in extract.extract_actions(bot)
                      if a["package"] and a["command"]})
    for pkg, cmd in actions:
        entries.append(_entry(
            "schema", "action",
            f"Action `{pkg}.{cmd}` present.",
            True, version, ev, attested))

    # --- Observational fact: usage of THIS bot (OBSERVED, org fingerprint) ---
    entries.append(_entry(
        "organisation", "usage",
        f"Observed {len(packages)} package(s), {len(var_types)} variable type(s), "
        f"{len(actions)} distinct action(s).",
        False, version, ev, attested))

    return entries


def load_ledger(path: str) -> dict:
    """Read the ingest ledger (hash -> record) from ``path``; ``{}`` when absent.

    Read-only, like the rest of the package. A missing or malformed ledger reads
    as empty so a first ingest just works.
    """
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def plan(bot: Any, *, attested: bool = False, ledger: dict | None = None,
         source: str | None = None) -> dict:
    """Compute the ingest plan for one bot. Deterministic and read-only.

    ``ledger`` maps a bot ``hash`` to its record (see ``load_ledger``). When this
    bot's hash is already present the plan is an idempotent no-op: it proposes no
    entries and no ledger line, so re-ingesting the same bot changes nothing.
    """
    h = bot_hash(bot)
    name, version = _identity(bot)
    provenance = "attested-export" if attested else "observed"
    noop = bool(ledger) and h in ledger
    return {
        "hash": h,
        "name": name,
        "version": version,
        "provenance": provenance,
        "idempotent_noop": noop,
        "entries": [] if noop else _entries(bot, version, h, attested),
        # first_seen is stamped when the line is written to the ledger, not here,
        # so plan() stays deterministic. No new line for an already-ingested bot.
        "ledger_line": None if noop else {
            "hash": h,
            "name": name,
            "version": version,
            "provenance": provenance,
            "source": source,
        },
    }
