"""Extract packages, actions, and variables from a bot dict (read-only).

Thin wrappers over the deep ``model.Bot`` seam, kept for the CLI ``extract``
command and existing call sites. They build a throwaway ``Bot``; a consumer that
reads several collections of the same bot should build one ``model.Bot`` itself
and read its cached properties, rather than calling these repeatedly.

Schema-tolerant: see ``model.py``. Results are JSON-serialisable and
deterministically ordered.
"""

from __future__ import annotations

from typing import Any

from . import model


def extract_packages(bot: Any) -> list[dict]:
    """Declared packages as sorted [{name, version}] (version may be None)."""
    return model.Bot.of(bot).packages


def extract_actions(bot: Any) -> list[dict]:
    """Every detected action node as sorted [{package, command, category}]."""
    return model.Bot.of(bot).actions


def action_usage(bot: Any) -> list[dict]:
    """Aggregated action usage: [{package, command, count}] sorted by count desc."""
    return model.Bot.of(bot).action_usage


def extract_variables(bot: Any) -> list[dict]:
    """Bot variables as sorted [{name, type, input, output}]."""
    return model.Bot.of(bot).variables


def variable_names(bot: Any) -> set[str]:
    return model.Bot.of(bot).variable_names


def extract_all(bot: Any) -> dict:
    """Everything, plus a note when nothing recognisable was found."""
    b = model.Bot.of(bot)
    result = {
        "packages": b.packages,
        "actions": b.action_usage,
        "action_count": len(b.actions),
        "variables": b.variables,
    }
    if not b.packages and not b.actions and not b.variables:
        result["note"] = (
            "No packages, actions, or variables recognised. The document may use "
            "a schema this heuristic tool does not yet know; see "
            "knowledge/schema/a360-bot-json.md."
        )
    return result
