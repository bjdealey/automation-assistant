"""Deterministic complexity metrics for a bot (read-only).

Metrics are structural proxies, not a quality verdict. Use them to locate
hotspots for skills ``08-bot-review`` and ``14-performance-review``.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from . import extract, model


def metrics(bot: Any) -> dict:
    actions = extract.extract_actions(bot)
    categories = Counter(a["category"] for a in actions)
    variables = extract.extract_variables(bot)
    packages = extract.extract_packages(bot)

    m = {
        "action_count": len(actions),
        "distinct_commands": len({(a["package"], a["command"]) for a in actions}),
        "distinct_packages": len(packages),
        "variable_count": len(variables),
        "loops": categories.get("loop", 0),
        "conditionals": categories.get("conditional", 0),
        "error_handlers": categories.get("error", 0),
        "sub_bot_calls": categories.get("runtask", 0),
        "fixed_waits": categories.get("wait", 0),
        "max_json_depth": model.json_depth(bot),
    }
    # A simple, documented, deterministic score. Higher = more to reason about.
    m["complexity_score"] = (
        m["action_count"]
        + 3 * m["loops"]
        + 2 * m["conditionals"]
        + 2 * m["error_handlers"]
        + m["variable_count"]
    )
    m["_note"] = (
        "Structural proxy only. loops/conditionals/error handlers are detected by "
        "heuristic command classification (INFERRED)."
    )
    return m
