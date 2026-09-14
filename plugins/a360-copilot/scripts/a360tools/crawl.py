"""Crawl a folder for candidate bot files (read-only)."""

from __future__ import annotations

import os
from typing import Any, Iterable

from . import model


def find_bot_files(root: str, extensions: Iterable[str] = model.BOT_EXTENSIONS
                   ) -> list[dict]:
    """Recursively list candidate bot files under ``root``.

    Returns sorted [{path, relpath, size, ext}]. A single file path is allowed.
    """
    exts = tuple(e.lower() for e in extensions)
    results = []

    if os.path.isfile(root):
        candidates = [root]
        base = os.path.dirname(root) or "."
    else:
        candidates = []
        base = root
        for dirpath, dirnames, filenames in os.walk(root):
            # deterministic traversal; skip hidden/VCS dirs
            dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
            for fn in sorted(filenames):
                if fn.lower().endswith(exts):
                    candidates.append(os.path.join(dirpath, fn))

    for path in candidates:
        try:
            size = os.path.getsize(path)
        except OSError:
            size = None
        _, ext = os.path.splitext(path)
        results.append({
            "path": path,
            "relpath": os.path.relpath(path, base),
            "size": size,
            "ext": ext.lower(),
        })
    return sorted(results, key=lambda r: r["path"])


def load_bot_files(root: str) -> tuple[list[tuple[dict, Any]], list[dict]]:
    """Discover and parse every bot file under ``root`` (or a single file).

    Returns ``(loaded, errors)``: ``loaded`` is [(file_row, parsed_bot)] for each
    file that parsed; ``errors`` is [{"path", "error"}] for each that did not. One
    unreadable file never aborts the walk. Order follows ``find_bot_files``.

    The single corpus-loading seam, shared by ``inventory`` and
    ``ingest.plan_corpus`` so the load-error policy lives in one place.
    """
    loaded: list[tuple[dict, Any]] = []
    errors: list[dict] = []
    for f in find_bot_files(root):
        try:
            data = model.load_bot(f["path"])
        except model.BotLoadError as exc:
            errors.append({"path": f["path"], "error": str(exc)})
            continue
        loaded.append((f, data))
    return loaded, errors
