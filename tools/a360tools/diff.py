"""Structural diff between two bot versions (read-only).

Compares packages, variables, and action usage as sets/multisets rather than by
node identity, so it is robust to reordering and to unknown node-id schemes.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from . import extract


def _versions_by_name(pkgs: list[dict]) -> dict[str, list]:
    """name -> sorted, de-duplicated list of the versions seen for it.

    ``extract_packages`` de-dups on (name, version), so one name can legitimately
    carry several versions. Group them, rather than letting a name-keyed dict
    silently drop all but the last.
    """
    m: dict[str, set] = {}
    for p in pkgs:
        m.setdefault(p["name"], set()).add(p["version"])
    return {n: sorted(vs, key=lambda v: v or "") for n, vs in m.items()}


def diff_bots(old: Any, new: Any) -> dict:
    old_pkgs = _versions_by_name(extract.extract_packages(old))
    new_pkgs = _versions_by_name(extract.extract_packages(new))
    pkg_added = sorted(set(new_pkgs) - set(old_pkgs))
    pkg_removed = sorted(set(old_pkgs) - set(new_pkgs))
    pkg_version_changed = sorted(
        (
            {"name": n, "old": old_pkgs[n], "new": new_pkgs[n]}
            for n in set(old_pkgs) & set(new_pkgs)
            if old_pkgs[n] != new_pkgs[n]
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
