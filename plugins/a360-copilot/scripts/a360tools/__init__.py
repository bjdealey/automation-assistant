"""a360tools — deterministic, schema-tolerant utilities for A360 bot JSON.

Read-only analysis (crawl, inventory, extract, deps, complexity, diff, validate)
plus a JSON normaliser. The exact A360 schema is not yet CONFIRMED, so the
extractors discover structure heuristically and say so; tighten them as the
schema in ``knowledge/schema/a360-bot-json.md`` is validated.

No third-party dependencies (Python standard library only).
"""

from __future__ import annotations

__version__ = "0.1.0"

from .model import BotLoadError, load_bot  # noqa: E402,F401
