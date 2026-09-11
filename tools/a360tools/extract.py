"""Extract packages, actions, and variables from a bot dict (read-only).

Schema-tolerant: see ``model.py``. Results are JSON-serialisable and
deterministically ordered.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from . import model


def extract_packages(bot: Any) -> list[dict]:
    """Declared packages as sorted [{name, version}] (version may be None)."""
    out = []
    for pkg in model.find_list_of_dicts(bot, model.PACKAGES_KEYS):
        name = model.get_ci(pkg, *model.NAME_KEYS)
        if not isinstance(name, str):
            continue
        version = model.get_ci(pkg, *model.VERSION_KEYS)
        out.append({"name": name, "version": version if isinstance(version, str) else None})
    # de-duplicate, stable order
    seen = {}
    for p in out:
        seen[(p["name"], p["version"])] = p
    return sorted(seen.values(), key=lambda p: (p["name"], p["version"] or ""))


def extract_actions(bot: Any) -> list[dict]:
    """Every detected action node as sorted [{package, command, category}]."""
    rows = []
    for _, d in model.iter_dicts(bot):
        if model.is_action_node(d):
            pkg = model.node_package(d)
            cmd = model.node_command(d)
            rows.append({
                "package": pkg,
                "command": cmd,
                "category": model.classify_command(pkg, cmd),
            })
    return sorted(rows, key=lambda r: (r["package"] or "", r["command"] or ""))


def action_usage(bot: Any) -> list[dict]:
    """Aggregated action usage: [{package, command, count}] sorted by count desc."""
    counts = Counter((r["package"], r["command"]) for r in extract_actions(bot))
    rows = [{"package": p, "command": c, "count": n} for (p, c), n in counts.items()]
    return sorted(rows, key=lambda r: (-r["count"], r["package"] or "", r["command"] or ""))


def extract_variables(bot: Any) -> list[dict]:
    """Bot variables as sorted [{name, type, input, output}]."""
    out = []
    for var in model.find_list_of_dicts(bot, model.VARIABLES_KEYS):
        name = model.get_ci(var, *model.NAME_KEYS)
        if not isinstance(name, str):
            continue
        vtype = model.get_ci(var, *model.TYPE_KEYS)
        out.append({
            "name": name,
            "type": vtype if isinstance(vtype, str) else None,
            "input": bool(model.get_ci(var, "input", "isinput")),
            "output": bool(model.get_ci(var, "output", "isoutput")),
        })
    seen = {}
    for v in out:
        seen[v["name"]] = v  # last definition wins; names should be unique
    return sorted(seen.values(), key=lambda v: v["name"])


def variable_names(bot: Any) -> set[str]:
    return {v["name"] for v in extract_variables(bot)}


def extract_all(bot: Any) -> dict:
    """Everything, plus a note when nothing recognisable was found."""
    packages = extract_packages(bot)
    actions = extract_actions(bot)
    variables = extract_variables(bot)
    result = {
        "packages": packages,
        "actions": action_usage(bot),
        "action_count": len(actions),
        "variables": variables,
    }
    if not packages and not actions and not variables:
        result["note"] = (
            "No packages, actions, or variables recognised. The document may use "
            "a schema this heuristic tool does not yet know; see "
            "knowledge/schema/a360-bot-json.md."
        )
    return result
