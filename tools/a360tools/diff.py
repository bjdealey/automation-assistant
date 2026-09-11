"""Structural diff between two bot versions (read-only).

Compares packages, variables, and action usage as sets/multisets rather than by
node identity, so it is robust to reordering and to unknown node-id schemes.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from . import extract


def _pkg_key(p: dict) -> tuple:
    return (p["name"], p["version"])


def diff_bots(old: Any, new: Any) -> dict:
    old_pkgs = {p["name"]: p for p in extract.extract_packages(old)}
    new_pkgs = {p["name"]: p for p in extract.extract_packages(new)}
    pkg_added = sorted(set(new_pkgs) - set(old_pkgs))
    pkg_removed = sorted(set(old_pkgs) - set(new_pkgs))
    pkg_version_changed = sorted(
        (
            {"name": n, "old": old_pkgs[n]["version"], "new": new_pkgs[n]["version"]}
            for n in set(old_pkgs) & set(new_pkgs)
            if old_pkgs[n]["version"] != new_pkgs[n]["version"]
        ),
        key=lambda r: r["name"],
    )

    old_vars = {v["name"]: v for v in extract.extract_variables(old)}
    new_vars = {v["name"]: v for v in extract.extract_variables(new)}
    var_added = sorted(set(new_vars) - set(old_vars))
    var_removed = sorted(set(old_vars) - set(new_vars))
    var_type_changed = sorted(
        (
            {"name": n, "old": old_vars[n]["type"], "new": new_vars[n]["type"]}
            for n in set(old_vars) & set(new_vars)
            if old_vars[n]["type"] != new_vars[n]["type"]
        ),
        key=lambda r: r["name"],
    )

    old_act = Counter((a["package"], a["command"]) for a in extract.extract_actions(old))
    new_act = Counter((a["package"], a["command"]) for a in extract.extract_actions(new))
    added_actions = sorted(
        (
            {"package": p, "command": c, "delta": (new_act[(p, c)] - old_act[(p, c)])}
            for (p, c) in (set(old_act) | set(new_act))
            if new_act[(p, c)] != old_act[(p, c)]
        ),
        key=lambda r: (r["package"] or "", r["command"] or ""),
    )

    return {
        "packages": {
            "added": pkg_added,
            "removed": pkg_removed,
            "version_changed": pkg_version_changed,
        },
        "variables": {
            "added": var_added,
            "removed": var_removed,
            "type_changed": var_type_changed,
        },
        "actions": {
            "usage_changed": added_actions,  # delta = new_count - old_count
            "total_old": sum(old_act.values()),
            "total_new": sum(new_act.values()),
        },
        "changed": bool(
            pkg_added or pkg_removed or pkg_version_changed
            or var_added or var_removed or var_type_changed or added_actions
        ),
    }
