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
from collections import Counter
from functools import cached_property
from typing import Any, Callable, Iterator

# --- Candidate key names (case-insensitive). Keep small to avoid false hits. ---
PACKAGE_KEYS = ("packagename", "package")
COMMAND_KEYS = ("commandname", "command")
NODES_KEYS = ("nodes", "commands", "childnodes")
VARIABLES_KEYS = ("variables", "variableslist", "botvariables")
PACKAGES_KEYS = ("packages", "packagelist", "importedpackages")
NAME_KEYS = ("name", "variablename")
TYPE_KEYS = ("type", "variabletype", "vartype")
VERSION_KEYS = ("version",)
VALUE_KEYS = ("value", "input", "defaultvalue", "default")

# A360 variable-reference token. CONFIRMED against a real export: a reference is
# ``$`` + optional ``@`` (global-value marker) + the variable name + an optional
# *structured* accessor tail before the closing ``$``. Observed tails: a type
# method (``$strTaskName.String:trim$``), a record field (``$recRunConfig{sEnv}$``),
# a namespace member (``$System:AATaskName$``) and none (``$strBatch$``).
#
# The tail char class is deliberately narrow (word chars and ``. : { } [ ]``): it
# must NOT span whitespace, quotes or operators, or a token would swallow embedded
# VBScript/PowerShell (``$cpu``, ``$_`` …) between two unrelated ``$`` and produce
# bogus references. Group 1 = the ``@`` marker (or empty), group 2 = the variable
# name, group 3 = the accessor tail (used to drop namespaced refs, e.g. System:).
VAR_REF_RE = re.compile(r"\$(@)?([A-Za-z_][A-Za-z0-9_]*)([\w.:{}\[\]]*)\$")

# The one absolute-path recogniser, shared by validate + dependencies (they had
# drifted copies — validate's lacked the POSIX branch). Windows drive | UNC | POSIX.
ABS_PATH_RE = re.compile(r"^[A-Za-z]:[\\/]|^\\\\[^\\]+\\|^/[^/ ]")


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


def looks_like_bot(obj: Any) -> bool:
    """True if ``obj`` is a parsed A360 taskbot: a dict with a top-level node list.

    Distinguishes a taskbot from an export ``manifest.json`` (keys
    ``files``/``packages``/``globalValues`` — no ``nodes``), so discovery can
    accept extensionless taskbot files without also matching the manifest.
    CONFIRMED against a real Control Room export (5/5 taskbots carry a top-level
    ``nodes`` list; the manifest does not).
    """
    return isinstance(obj, dict) and isinstance(get_ci(obj, *NODES_KEYS), list)


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


def var_ref_names(s: str, include_globals: bool = False) -> list[str]:
    """Variable names referenced by ``$..$`` tokens in ``s``, in order.

    Returns the leading identifier of each token, so plain (``$var$``), method
    (``$var.Type:method$``) and record-field (``$var{field}$``) forms all resolve
    to the base variable name. Global-value references (``$@name$``) are excluded
    unless ``include_globals`` is set, because they resolve to Control Room
    globals rather than the bot's own declared variables.
    """
    names = []
    for at, name, tail in VAR_REF_RE.findall(s):
        if at and not include_globals:
            continue  # $@global$ — Control Room global, not a declared bot var
        if tail.startswith(":"):
            continue  # $Namespace:member$ (e.g. System:) — not a declared bot var
        names.append(name)
    return names


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


# --------------------------------- Bot model ---------------------------------

class Bot:
    """A parsed A360 bot: one raw JSON document with its derived collections
    computed once and cached. The single deep seam the extractors read through —
    construct with ``Bot.of(json)``, then read ``.packages`` / ``.actions`` /
    ``.variables`` / ``.string_leaves`` / etc.

    Schema-tolerant (an unrecognised document yields empty collections, never an
    exception) and read-only (never mutates the raw document). Every collection
    is deterministically ordered, matching the free ``extract`` functions that
    now delegate here.
    """

    def __init__(self, raw: Any) -> None:
        self.raw = raw

    @classmethod
    def of(cls, raw: Any) -> "Bot":
        return cls(raw)

    @cached_property
    def dicts(self) -> list[tuple[str, dict]]:
        """(json_path, dict) for every dict in the document, pre-order."""
        return list(iter_dicts(self.raw))

    @cached_property
    def string_leaves(self) -> list[tuple[str, str | None, str]]:
        """(json_path, parent_key, value) for every string leaf."""
        return list(iter_strings(self.raw))

    @cached_property
    def action_nodes(self) -> list[tuple[str, dict]]:
        """(json_path, dict) for every dict that looks like an action node."""
        return [(p, d) for p, d in self.dicts if is_action_node(d)]

    @cached_property
    def packages(self) -> list[dict]:
        """Declared packages as sorted [{name, version}] (version may be None)."""
        out = []
        for pkg in find_list_of_dicts(self.raw, PACKAGES_KEYS):
            name = get_ci(pkg, *NAME_KEYS)
            if not isinstance(name, str):
                continue
            version = get_ci(pkg, *VERSION_KEYS)
            out.append({"name": name,
                        "version": version if isinstance(version, str) else None})
        seen = {}
        for p in out:
            seen[(p["name"], p["version"])] = p
        return sorted(seen.values(), key=lambda p: (p["name"], p["version"] or ""))

    @cached_property
    def variables(self) -> list[dict]:
        """Bot variables as sorted [{name, type, input, output}]."""
        out = []
        for var in find_list_of_dicts(self.raw, VARIABLES_KEYS):
            name = get_ci(var, *NAME_KEYS)
            if not isinstance(name, str):
                continue
            vtype = get_ci(var, *TYPE_KEYS)
            out.append({
                "name": name,
                "type": vtype if isinstance(vtype, str) else None,
                "input": bool(get_ci(var, "input", "isinput")),
                "output": bool(get_ci(var, "output", "isoutput")),
            })
        seen = {}
        for v in out:
            seen[v["name"]] = v  # last definition wins; names should be unique
        return sorted(seen.values(), key=lambda v: v["name"])

    @cached_property
    def actions(self) -> list[dict]:
        """Every detected action node as sorted [{package, command, category}]."""
        rows = []
        for _, d in self.action_nodes:
            pkg = node_package(d)
            cmd = node_command(d)
            rows.append({"package": pkg, "command": cmd,
                         "category": classify_command(pkg, cmd)})
        return sorted(rows, key=lambda r: (r["package"] or "", r["command"] or ""))

    @cached_property
    def action_usage(self) -> list[dict]:
        """Aggregated action usage [{package, command, count}], count desc."""
        counts = Counter((r["package"], r["command"]) for r in self.actions)
        rows = [{"package": p, "command": c, "count": n} for (p, c), n in counts.items()]
        return sorted(rows, key=lambda r: (-r["count"], r["package"] or "", r["command"] or ""))

    @property
    def variable_names(self) -> set[str]:
        return {v["name"] for v in self.variables}

    @cached_property
    def depth(self) -> int:
        return json_depth(self.raw)
