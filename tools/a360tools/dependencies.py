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

from . import extract, model

# Heuristic file-extension set (non-exhaustive; excludes .bot which is a sub-bot).
FILE_EXTS = (
    ".xlsx", ".xls", ".xlsm", ".csv", ".txt", ".pdf", ".json", ".xml",
    ".docx", ".doc", ".zip", ".log", ".html", ".htm", ".dat", ".png", ".jpg",
)
_ABS_PATH_RE = re.compile(r"""^[A-Za-z]:[\\/]|^\\\\[^\\]+\\|^/[^/ ]""")
_URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
_CRED_HINT_RE = re.compile(r"credential|locker|vault", re.IGNORECASE)


def _string_leaves(bot: Any) -> list[tuple[str, str | None, str]]:
    return list(model.iter_strings(bot))


def sub_bots(bot: Any) -> list[dict]:
    """Candidate sub-bot references: any string ending in .bot."""
    found = {}
    for path, _key, val in _string_leaves(bot):
        if val.lower().endswith(".bot"):
            found.setdefault(val, path)
    return sorted(
        ({"reference": ref, "at": at} for ref, at in found.items()),
        key=lambda r: r["reference"],
    )


def files(bot: Any) -> list[dict]:
    """Candidate file/folder paths referenced as literals."""
    found = {}
    for path, _key, val in _string_leaves(bot):
        low = val.lower()
        if low.endswith(".bot"):
            continue  # that's a sub-bot
        if low.endswith(FILE_EXTS) or _ABS_PATH_RE.search(val):
            found.setdefault(val, path)
    return sorted(
        ({"reference": ref, "at": at} for ref, at in found.items()),
        key=lambda r: r["reference"],
    )


def urls(bot: Any) -> list[dict]:
    """External URLs referenced as literals (a proxy for external systems)."""
    found = {}
    for path, _key, val in _string_leaves(bot):
        for m in _URL_RE.findall(val):
            found.setdefault(m, path)
    return sorted(
        ({"reference": ref, "at": at} for ref, at in found.items()),
        key=lambda r: r["reference"],
    )


def credentials(bot: Any) -> list[dict]:
    """Candidate credential usages: CREDENTIAL-typed vars or credential-hinted keys."""
    out = []
    for var in extract.extract_variables(bot):
        if var["type"] and "credential" in var["type"].lower():
            out.append({"kind": "variable", "reference": var["name"], "at": "variables"})
    for path, key, _val in _string_leaves(bot):
        if key and _CRED_HINT_RE.search(key):
            out.append({"kind": "reference", "reference": key, "at": path})
    # de-dup
    seen = {(r["kind"], r["reference"], r["at"]): r for r in out}
    return sorted(seen.values(), key=lambda r: (r["kind"], r["reference"]))


def extract_dependencies(bot: Any) -> dict:
    """All dependency edges for one bot."""
    return {
        "packages": extract.extract_packages(bot),
        "sub_bots": sub_bots(bot),
        "files": files(bot),
        "urls": urls(bot),
        "credentials": credentials(bot),
        "_method": "heuristic; file/sub-bot/credential detection may be incomplete "
                   "until the schema is CONFIRMED",
    }
