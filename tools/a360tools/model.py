"""Schema-tolerant traversal helpers for A360 bot JSON.

The exact A360 bot JSON schema is not yet CONFIRMED (see
``knowledge/schema/a360-bot-json.md``). These helpers therefore *discover*
structure by walking the JSON and matching a small set of candidate key names,
rather than assuming an exact shape. They degrade gracefully: an unrecognised
document yields empty results, never an exception.

All matching is case-insensitive. As the schema is confirmed, tighten the
candidate sets below and add regression tests.

Nothing here mutates its input.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Iterator

# --- Candidate key names (case-insensitive). Keep small to avoid false hits. ---
PACKAGE_KEYS = ("packagename", "package")
COMMAND_KEYS = ("commandname", "command")
VARIABLES_KEYS = ("variables", "variableslist", "botvariables")
PACKAGES_KEYS = ("packages", "packagelist", "importedpackages")
NAME_KEYS = ("name", "variablename")
TYPE_KEYS = ("type", "variabletype", "vartype")
VERSION_KEYS = ("version",)
VALUE_KEYS = ("value", "input", "defaultvalue", "default")

# Files that look like bots vs. plain JSON; both are attempted as JSON.
BOT_EXTENSIONS = (".bot", ".json")

# A variable reference token hypothesis: $name$ (INFERRED — confirm from export).
VAR_REF_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)\$")


class BotLoadError(Exception):
    """Raised when a bot file cannot be read or parsed as JSON."""


def load_bot(path: str) -> dict:
    """Read and parse a bot file as JSON. Raises BotLoadError on failure."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError as exc:
        raise BotLoadError(f"file not found: {path}") from exc
    except UnicodeDecodeError as exc:
        raise BotLoadError(f"not UTF-8 text: {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise BotLoadError(f"invalid JSON: {path}: {exc}") from exc
    return data


def normalized_json(bot: Any) -> str:
    """Canonical, stable JSON text for a bot: sorted keys, 2-space indent.

    The single source of normalisation, shared by the ``normalize`` command and
    by ingest hashing, so identical bots always produce identical bytes
    regardless of original key order or whitespace.
    """
    return json.dumps(bot, indent=2, ensure_ascii=False, sort_keys=True)


# ----------------------------- case-insensitive get -----------------------------

def get_ci(d: dict, *candidates: str) -> Any:
    """Return d[k] for the first key (case-insensitively) matching a candidate."""
    if not isinstance(d, dict):
        return None
    lowered = {str(k).lower(): k for k in d.keys()}
    for cand in candidates:
        real = lowered.get(cand.lower())
        if real is not None:
            return d[real]
    return None


def has_ci(d: dict, *candidates: str) -> bool:
    if not isinstance(d, dict):
        return False
    lowered = {str(k).lower() for k in d.keys()}
    return any(c.lower() in lowered for c in candidates)


# --------------------------------- walkers ---------------------------------

def iter_dicts(obj: Any, path: str = "$") -> Iterator[tuple[str, dict]]:
    """Yield (json_path, dict) for every dict in the structure, pre-order."""
    if isinstance(obj, dict):
        yield path, obj
        for k, v in obj.items():
            yield from iter_dicts(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_dicts(v, f"{path}[{i}]")


def iter_strings(obj: Any, path: str = "$", key: str | None = None
                 ) -> Iterator[tuple[str, str | None, str]]:
    """Yield (json_path, parent_key, value) for every string in the structure.

    parent_key is the dict key the string sits under, or None inside a list.
    """
    if isinstance(obj, str):
        yield path, key, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from iter_strings(v, f"{path}.{k}", str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_strings(v, f"{path}[{i}]", None)


def json_depth(obj: Any) -> int:
    """Maximum nesting depth of dicts/lists (a rough structural-complexity proxy)."""
    if isinstance(obj, dict):
        return 1 + max((json_depth(v) for v in obj.values()), default=0)
    if isinstance(obj, list):
        return 1 + max((json_depth(v) for v in obj), default=0)
    return 0


# ------------------------------- predicates -------------------------------

def is_action_node(d: Any) -> bool:
    """A dict that names both a package and a command looks like an action node."""
    return isinstance(d, dict) and has_ci(d, *PACKAGE_KEYS) and has_ci(d, *COMMAND_KEYS)


def node_package(d: dict) -> str | None:
    v = get_ci(d, *PACKAGE_KEYS)
    return v if isinstance(v, str) else None


def node_command(d: dict) -> str | None:
    v = get_ci(d, *COMMAND_KEYS)
    return v if isinstance(v, str) else None


def find_list_of_dicts(obj: Any, keys: tuple[str, ...]) -> list[dict]:
    """Find the first list-of-dicts stored under any of ``keys`` (case-insensitive).

    Searches the whole structure (not just the top level) so it tolerates the
    collection being nested.
    """
    for _, d in iter_dicts(obj):
        val = get_ci(d, *keys)
        if isinstance(val, list) and any(isinstance(x, dict) for x in val):
            return [x for x in val if isinstance(x, dict)]
    return []


def attribute_pair(d: dict) -> tuple[str, Any] | None:
    """If d looks like a named attribute, return (name, value_node), else None."""
    name = get_ci(d, *NAME_KEYS)
    if not isinstance(name, str):
        return None
    if not has_ci(d, *VALUE_KEYS):
        return None
    return name, get_ci(d, *VALUE_KEYS)


def scalar_strings_in(node: Any) -> list[str]:
    """All string leaves within a (possibly nested) value node."""
    return [s for _, _, s in iter_strings(node)]


def is_variable_reference(s: str) -> bool:
    return bool(VAR_REF_RE.search(s))


# ------------------------- command classification (heuristic) -------------------------
# These are INFERRED groupings; confirm command tokens against real exports.

def _norm(s: str | None) -> str:
    return re.sub(r"[\s_]+", "", (s or "").lower())


def classify_command(package: str | None, command: str | None) -> str:
    """Best-effort category for an action: loop|conditional|error|runtask|wait|other."""
    p, c = _norm(package), _norm(command)
    blob = f"{p}:{c}"
    if "runtask" in blob or "runbot" in blob or c in {"runtask", "runtaskbot"}:
        return "runtask"
    if "loop" in blob or c in {"foreach", "while", "each"}:
        return "loop"
    if "trycatch" in blob or "errorhandler" in blob or c in {"try", "catch", "finally"}:
        return "error"
    if c in {"if", "elseif", "else"} or "decision" in blob or blob.endswith(":if"):
        return "conditional"
    if any(w in blob for w in ("delay", "pause", "sleep", "wait")):
        return "wait"
    return "other"
