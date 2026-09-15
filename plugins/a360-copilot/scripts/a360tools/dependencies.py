"""Extract a bot's outbound dependencies (read-only, heuristic).

Produces the edges for the dependency chain described in skill
``11-dependency-analysis``:

    BOT -> SUB-BOT / PACKAGE / VARIABLE / APPLICATION / FILE / CREDENTIAL / SYSTEM

Because the schema is not yet CONFIRMED, file / sub-bot / credential detection is
heuristic and may be incomplete. Each result set says how it was found.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import unquote

from . import model

# Heuristic file-extension set (non-exhaustive; excludes .bot which is a sub-bot).
FILE_EXTS = (
    ".xlsx", ".xls", ".xlsm", ".csv", ".txt", ".pdf", ".json", ".xml",
    ".docx", ".doc", ".zip", ".log", ".html", ".htm", ".dat", ".png", ".jpg",
)
_URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
_CRED_HINT_RE = re.compile(r"credential|locker|vault", re.IGNORECASE)


def sub_bots(b: model.Bot) -> list[dict]:
    """Candidate sub-bot references.

    Two reference styles are recognised:

    * A ``repository://`` path — how a real A360 ``TaskBot: runTask`` node stores
      the called bot (in the ``taskbotFile`` attribute), URL-encoded. CONFIRMED
      against a real Control Room export.
    * A string ending in ``.bot`` — the plain-path style.

    ``repository://`` references are URL-decoded so they match the bot's stored
    path (e.g. the export manifest / other bots' paths) for graph building.
    """
    found = {}
    for path, _key, val in b.string_leaves:
        low = val.lower()
        if low.startswith("repository://"):
            found.setdefault(unquote(val), path)
        elif low.endswith(".bot"):
            found.setdefault(val, path)
    return sorted(
        ({"reference": ref, "at": at} for ref, at in found.items()),
        key=lambda r: r["reference"],
    )


def files(b: model.Bot) -> list[dict]:
    """Candidate file/folder paths referenced as literals."""
    found = {}
    for path, _key, val in b.string_leaves:
        low = val.lower()
        if low.endswith(".bot"):
            continue  # that's a sub-bot
        if low.endswith(FILE_EXTS) or model.ABS_PATH_RE.search(val):
            found.setdefault(val, path)
    return sorted(
        ({"reference": ref, "at": at} for ref, at in found.items()),
        key=lambda r: r["reference"],
    )


def urls(b: model.Bot) -> list[dict]:
    """External URLs referenced as literals (a proxy for external systems)."""
    found = {}
    for path, _key, val in b.string_leaves:
        for m in _URL_RE.findall(val):
            found.setdefault(m, path)
    return sorted(
        ({"reference": ref, "at": at} for ref, at in found.items()),
        key=lambda r: r["reference"],
    )


def credentials(b: model.Bot) -> list[dict]:
    """Candidate credential usages: CREDENTIAL-typed vars or credential-hinted keys."""
    out = []
    for var in b.variables:
        if var["type"] and "credential" in var["type"].lower():
            out.append({"kind": "variable", "reference": var["name"], "at": "variables"})
    for path, key, _val in b.string_leaves:
        if key and _CRED_HINT_RE.search(key):
            out.append({"kind": "reference", "reference": key, "at": path})
    # de-dup
    seen = {(r["kind"], r["reference"], r["at"]): r for r in out}
    return sorted(seen.values(), key=lambda r: (r["kind"], r["reference"]))


def extract_dependencies(bot: Any) -> dict:
    """All dependency edges for one bot."""
    b = model.Bot.of(bot)
    return {
        "packages": b.packages,
        "sub_bots": sub_bots(b),
        "files": files(b),
        "urls": urls(b),
        "credentials": credentials(b),
        "_method": "heuristic; file/sub-bot/credential detection may be incomplete "
                   "until the schema is CONFIRMED",
    }
