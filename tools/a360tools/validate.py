"""Heuristic validation / hygiene report for a bot (read-only).

This is a *signal*, not a verdict. Because the A360 schema is not yet CONFIRMED,
every check here is heuristic; confidences reflect that. See skill
``06-bot-validation`` for how to use the output, and ``13-security-review`` for
the secret checks.

Secret findings NEVER include the secret value — only its location and the kind
of indicator that matched.
"""

from __future__ import annotations

import re
from typing import Any

from . import model

_SEVERITY_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}

_SECRET_KEY_RE = re.compile(
    r"pass(word|wd)?|secret|api[_-]?key|access[_-]?key|client[_-]?secret|"
    r"auth|token|conn(ection)?[_-]?str", re.IGNORECASE)

# High-signal secret *formats* (kept deliberately narrow to avoid flagging uids).
_FORMAT_DETECTORS = (
    ("aws_access_key_id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")),
)


def _finding(sev, check, location, message, confidence):
    return {"severity": sev, "check": check, "location": location,
            "message": message, "confidence": confidence}


def validate_bot(bot: Any) -> dict:
    findings: list[dict] = []
    b = model.Bot.of(bot)

    # 1. Was any structure recognised at all?
    recognised = bool(b.packages or b.actions or b.variables)
    if not recognised:
        findings.append(_finding(
            "MEDIUM", "structure", "$",
            "No packages/actions/variables recognised; the schema may differ from "
            "the heuristic model (knowledge/schema/a360-bot-json.md).", "LOW"))

    var_names = b.variable_names

    # 2. Secret indicators by attribute name.
    for path, d in b.dicts:
        pair = model.attribute_pair(d)
        if not pair:
            continue
        name, value_node = pair
        if _SECRET_KEY_RE.search(name):
            literals = [s for s in model.scalar_strings_in(value_node)
                        if s.strip() and not model.is_variable_reference(s)]
            if literals:
                findings.append(_finding(
                    "HIGH", "hardcoded_secret", f"{path} (attribute '{name}')",
                    "Attribute name suggests a secret and its value is a literal "
                    "(not a variable/Vault reference). Move to the Credential Vault "
                    "and rotate if it is live. [value not shown]", "MEDIUM"))

    # 3. Secret indicators by value format.
    for path, _key, val in b.string_leaves:
        for kind, rx in _FORMAT_DETECTORS:
            if rx.search(val):
                findings.append(_finding(
                    "HIGH", "hardcoded_secret", path,
                    f"Value matches a secret format ({kind}). Remove, move to the "
                    "Credential Vault, and rotate. [value not shown]", "MEDIUM"))
                break

    # 4. Variable-reference sanity ($name$ tokens vs declared variables).
    referenced: dict[str, str] = {}
    for path, _key, val in b.string_leaves:
        for tok in model.VAR_REF_RE.findall(val):
            referenced.setdefault(tok, path)
    if not referenced:
        findings.append(_finding(
            "INFO", "variable_refs", "$",
            "No $var$ tokens found. Variable-reference syntax is unconfirmed, so "
            "reference checking is inconclusive.", "LOW"))
    else:
        for tok, path in sorted(referenced.items()):
            if tok not in var_names:
                findings.append(_finding(
                    "MEDIUM", "undefined_variable", path,
                    f"Reference to '${tok}$' but no matching variable is declared "
                    "(reference syntax is INFERRED).", "LOW"))
        for name in sorted(var_names - set(referenced)):
            findings.append(_finding(
                "INFO", "unused_variable", "variables",
                f"Variable '{name}' is declared but not referenced via $..$ "
                "(inconclusive if references use another syntax).", "LOW"))

    # 5. Hard-coded absolute paths (maintainability).
    seen_paths = set()
    for path, _key, val in b.string_leaves:
        if model.ABS_PATH_RE.search(val) and val not in seen_paths:
            seen_paths.add(val)
            findings.append(_finding(
                "LOW", "hardcoded_path", path,
                "Absolute path literal; prefer a variable/config value for "
                "portability.", "MEDIUM"))

    # 6. Fixed waits (reliability/performance).
    for path, d in b.action_nodes:
        if model.classify_command(model.node_package(d), model.node_command(d)) == "wait":
            findings.append(_finding(
                "LOW", "fixed_wait", path,
                "Fixed delay/wait detected; prefer waiting for a condition.",
                "LOW"))

    findings.sort(key=lambda f: (_SEVERITY_RANK.get(f["severity"], 9),
                                 f["check"], f["location"]))

    summary = {sev: 0 for sev in _SEVERITY_RANK}
    for f in findings:
        summary[f["severity"]] += 1

    return {
        "json_parse": "OK",  # reaching here means it parsed
        "recognised": recognised,
        "summary": summary,
        "findings": findings,
        "_disclaimer": "Heuristic report against an INFERRED schema. Treat as a "
                       "signal; confirm each finding before acting.",
    }
