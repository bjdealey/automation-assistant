# A360 bot engineering standards

**Confidence:** these are engineering **best-practice candidates** — general
software/automation engineering applied to A360. They are the bar we design and
review against. They are *not* claims about platform behaviour; where a standard
depends on a platform capability, that capability must be `CONFIRMED` separately.

Use these as the checklist behind skills `05` (generation), `08` (review),
`09` (refactoring), `13` (security), and `14` (performance).

## Structure & architecture

- **Stage the workflow.** A bot should read as: input → validate → initialise →
  acquire → process → decide → act → verify → handle errors → cleanup → output.
- **Single responsibility.** Prefer small, focused, reusable sub-bots over one
  monolith. A sub-bot should do one nameable thing.
- **No magic values.** Paths, URLs, timeouts, thresholds, and credentials come
  from variables / config / the Credential Vault — never hard-coded inline.
- **Explicit inputs and outputs.** A bot's input and output variables are its
  contract; name and document them.

## Reliability

- **Every external interaction can fail.** Wrap I/O (files, apps, network, UI)
  in error handling with a defined recovery or a clean, logged failure.
- **No blind waits.** Prefer waiting for a condition/element over fixed sleeps;
  where a delay is unavoidable, make it a named, justified variable.
- **Idempotency & restartability.** Design so a re-run after failure does not
  double-process. Track progress (e.g. via a queue or status column).
- **Retries with intent.** Retry only transient failures, with bounded attempts
  and backoff; never retry a deterministic error forever.

## Maintainability

- **Consistent naming.** Follow the organisation's conventions (see
  `knowledge/organisation/`); when none exist, propose one and record it.
- **DRY.** Extract repeated sequences into sub-bots.
- **Readable configuration.** Group configuration/initialisation at the top.
- **Comment intent, not mechanics.** Explain *why*, not *what the action is*.

## Security

- **Credentials via the Vault**, never in variables, attributes, or logs.
- **Least privilege** for the runtime user and any service accounts.
- **Never log sensitive data** (PII, secrets, tokens). Mask before logging.
- **Validate external input** before using it in file paths, queries, or commands.
- **Clean up** temporary files that may contain sensitive data.

## Observability

- **Log stage transitions** with enough context to locate a failure (which
  record, which item, which step) — without logging sensitive values.
- **Capture failure context**: the action, inputs, and error, plus a screenshot
  where a UI is involved and permitted.
- **Make status auditable**: success/failure counts, items processed, run id.

## Performance

- **Minimise UI interaction.** Prefer APIs / direct data operations over
  screen automation where a `CONFIRMED` capability exists.
- **Do work once.** Hoist invariant work out of loops; batch where possible.
- **Manage applications deliberately.** Launch once, reuse, and close cleanly;
  don't relaunch per iteration.
- **Handle data efficiently.** Avoid repeatedly re-reading the same source;
  read once into a structured variable.

## Testability

- **Deterministic inputs.** Provide sample/fixture inputs for each path.
- **Cover the unhappy paths**, not just the golden path.
- **Isolate side effects** so tests can run without mutating production systems.

---

Each standard a bot violates becomes a review finding in the form:

`SEVERITY → LOCATION → PROBLEM → WHY IT MATTERS → RECOMMENDED CHANGE → CONFIDENCE`
