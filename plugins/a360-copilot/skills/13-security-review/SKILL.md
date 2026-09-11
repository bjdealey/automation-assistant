---
name: 13-security-review
description: Audit an A360 bot for security issues — hard-coded credentials and secrets, sensitive-data handling, logging of secrets/PII, unsafe file handling, and over-broad permissions. Use when asked to security-review a bot, check for exposed secrets, or assess data handling. Produces severity-ranked findings and uses a360tools validate secret heuristics as a starting signal only.
---

# 13 · Security review

**Goal:** find and prioritise security weaknesses in a bot.

## Checklist

- **Credentials:** are secrets pulled from the Credential Vault, never hard-coded
  in attributes/variables? Any literal passwords, API keys, tokens, connection
  strings?
- **Sensitive data:** is PII / financial / health data minimised, and not
  persisted or moved insecurely?
- **Logging:** are secrets or sensitive values written to logs / message boxes /
  screenshots? (They must be masked.)
- **File handling:** are paths validated? Any writing of sensitive data to
  world-readable / temp locations without cleanup? Any path built from
  unvalidated input (traversal risk)?
- **Input validation:** is external input validated before use in paths,
  queries, commands, or UI?
- **Permissions:** does the bot / runtime user have least privilege?
- **Third-party calls:** where does data leave the environment, and is that
  intended and secured?

## Deterministic assist (signal, not proof)

```bash
cd tools
python -m a360tools validate <bot_file>   # includes hard-coded-secret heuristics
```

Heuristics flag *candidates* (e.g. attribute values that look like keys/
passwords). Confirm each by inspection before reporting it as a finding, and
never paste a discovered secret into output — reference its location.

## Finding format

Same as `08-bot-review`: `SEVERITY → LOCATION → PROBLEM → WHY IT MATTERS →
RECOMMENDED CHANGE → CONFIDENCE`. Treat exposed live secrets as **CRITICAL** and
recommend rotation, not just removal.

## Guardrail

Do not exfiltrate or echo secrets. Report location + type; recommend Vault +
rotation.
