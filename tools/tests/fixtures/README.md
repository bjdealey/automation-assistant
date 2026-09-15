# Test fixtures

## `hypothesis_bot.json` — a HYPOTHESIS, not truth

This file encodes the **hypothesised** A360 bot-JSON shape described in
`knowledge/schema/a360-bot-json.md` (`packageName`/`commandName`/`attributes`
nodes, a `packages` list, `variables` with types). That shape is **`INFERRED`**
— it has **not** been confirmed against a real Automation Anywhere export.

**What the tests actually prove:** that the `a360tools` extractors behave
correctly on a *known-shape* input — packages/actions/variables are found,
dependencies and complexity are computed, the validator flags the planted
issues (a hard-coded secret, an undefined `$var$`, an absolute path, a fixed
wait) without leaking the secret value. They do **not** prove the schema is
right, because the fixture and the extractors share the same assumption.

**Do not read a green test suite as "the schema is correct."** It only means the
tooling is self-consistent with the hypothesis.

## When you get a real bot

The first real export (or even a pasted real bot) is the ground-truth trigger:

1. Save a **scrubbed** copy here as `real_<version>.bot` (e.g. `real_35.bot`) —
   scrub credentials/paths/PII first; real exports otherwise stay out of git
   (see `.gitignore` and `knowledge/bots/README.md`).
2. Add tests asserting the extractors work on the *real* shape.
3. Where the real shape differs from `hypothesis_bot.json`, correct the
   extractors in `a360tools/model.py`, promote the affected fields in
   `knowledge/schema/a360-bot-json.md` from `INFERRED`→`CONFIRMED`, and keep the
   hypothesis fixture only for the parts still unconfirmed.

## `real_botcode7.bot` — CONFIRMED shape, synthetic content

This fixture reproduces structures observed in a **real Control Room export**
(`botCodeVersion` 7, a Windows task bot): `nodes` with `uid`/`commandName`/
`packageName`/`attributes`/`children`/`returnTo`, attribute values typed
`STRING`/`NUMBER`/`TASKBOT` carrying a literal `string`/`number` or an
`expression`, a `TaskBot: runTask` node whose `taskbotFile` is a
`repository:///…` (URL-encoded) sub-bot path, `variables` with
`input`/`output`/`defaultValue`, real package names and versions, and a
`properties` block.

Unlike `hypothesis_bot.json`, this shape is **CONFIRMED** — it is what the
extractors are pinned to for real exports. Its *content*, however, is entirely
synthetic: names, paths, and the sub-bot reference are placeholders, and it
contains **no credentials, secrets, or PII**. That is deliberate — the real
export it was derived from carries live infrastructure detail (tenant IDs, API
endpoints, credential-locker names, phone numbers) and therefore stays **out of
git** per the scrub rule above. When you need to assert against a genuine bot,
scrub a copy first; do not commit a raw export.

It also exercises every A360 variable-reference form the tokenizer must handle:
plain `$var$`, type-method `$var.String:trim$`, record-field `$rec{field}$`,
global `$@Global$`, and namespace `$System:member$` — so the validator does not
raise false "undefined variable" findings on real bots.
