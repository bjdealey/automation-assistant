#!/bin/bash
# SessionStart hook — make a fresh Claude Code (web) session ready to work on
# a360tools. The package is Python-stdlib-only; the sole dev dependency is the
# test runner (pytest). This hook ensures pytest is available and that the
# package imports, so tests can be run immediately. Synchronous by design so the
# session starts in a known-good state (no race conditions).
set -euo pipefail

# Web / remote sessions only — local sessions manage their own environment.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}/tools"

# Ensure the test runner is present (idempotent; container state is cached after
# the hook completes, so later sessions start fast). Best-effort: a network
# hiccup shouldn't block the session — the import smoke-check below is the gate.
if ! python3 -m pytest --version >/dev/null 2>&1; then
  python3 -m pip install --quiet --disable-pip-version-check -r requirements-dev.txt \
    || echo "session-start: WARNING - could not install pytest; run 'pip install -r tools/requirements-dev.txt' by hand" >&2
fi

# Smoke-check: the package imports cleanly (this is the 'ready' signal).
python3 -c "import a360tools; print('session-start: a360tools', a360tools.__version__, 'import OK')"

echo "session-start: pytest $(python3 -m pytest --version 2>/dev/null || echo 'NOT INSTALLED')"
