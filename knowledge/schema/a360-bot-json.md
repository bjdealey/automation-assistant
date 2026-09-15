# A360 bot JSON — working model

> **Confidence for this document: `MIXED`.**
> The core structure below is now **`CONFIRMED`** against a real Control Room
> export (see *Ground truth* box). Fields that the export did not exercise
> (populated triggers, the full type-token set, some attribute payloads) remain
> **`INFERRED`** or **`UNKNOWN`** and are tagged inline. Do not treat an
> `INFERRED` field as fact; correct it from the next export that exercises it.
>
> **Ground truth:** first real Control Room export ingested **2026-09-15** — 5
> Windows task bots (`contentType: application/vnd.aa.taskbot`), bot format
> `properties.botCodeVersion = "7"`. The raw export carries live infrastructure
> detail (tenant IDs, API endpoints, credential lockers, PII) and stays **out of
> git** per the scrub rule. The committed evidence is the synthetic-content,
> real-shape fixture [`tools/tests/fixtures/real_botcode7.bot`](../../tools/tests/fixtures/real_botcode7.bot),
> which the `a360tools` tests pin the extractors to.
>
> **A360 platform version:** still `UNKNOWN`. `botCodeVersion` is the *bot format*
> version (7), **not** the Control Room platform version (e.g. 35.x); the export
> does not state the platform version. Record it here once known.

The purpose of this file is to give the copilot and the tools a shape to look
for, and a checklist for validating that shape.

---

## 1. Obtaining more ground truth

The first export is ingested; the structure below is confirmed. To extend it:

1. Export a bot that exercises a construct not yet confirmed here (a **populated
   trigger**, a `DATETIME`/`WINDOW`/`SESSION`/`TABLE` variable, a message box).
2. `python -m a360tools normalize <file>` for a stable, readable form.
3. Where it differs from §2–§5, correct `a360tools/model.py` + tests and promote
   the affected field here, citing the export.

**GUI → stored representation → JSON → runtime** is the mapping we are building.

---

## 2. File & top-level shape (`CONFIRMED`)

A task bot (`.bot`) is a single UTF-8 JSON object. In a Control Room export the
file is **extensionless**, sits under an `Automation Anywhere/Bots/...` path, and
is accompanied by a `manifest.json` (not a bot) and per-node preview PNGs.

Top-level keys (all six present in every task bot observed):

```jsonc
{
  "triggers": [],                 // list; empty in every bot seen (see §6)
  "nodes":    [ /* ordered task steps — §3 */ ],
  "variables":[ /* §4 */ ],
  "packages": [ /* §5 */ ],
  "properties": {                 // §2.1
    "botCodeVersion": "7",
    "improvedNumberSupport": true,
    "timeout": "0s",
    "automationPriority": "PRIORITY_MEDIUM",
    "runInChildWindow": false,
    "runInChildWindowMode": "DESKTOP"
  },
  "workItemTemplateName": null    // null when the bot is not a queue processor
}
```

> The earlier hypothesis of a top-level `metadata` object was **wrong**: bot-level
> settings live in `properties`, and there is no `metadata` key.

### 2.1 `properties` (`CONFIRMED` keys; value semantics partly `INFERRED`)

`botCodeVersion` (string) is the bot format version — `"7"` in this export.
`timeout` is a duration string (`"0s"` = no timeout). `automationPriority` is an
enum (`PRIORITY_MEDIUM` seen; other levels `INFERRED`). `runInChildWindow` /
`runInChildWindowMode` control the run surface. `improvedNumberSupport` is a
boolean bot flag.

---

## 3. Nodes / steps (`CONFIRMED`)

Each step is an object. Confirmed keys:

| Concept | JSON key | Notes |
|---------|----------|-------|
| Identity | `uid` | UUID; stable id used for references/ordering. |
| Package | `packageName` | e.g. `String`, `TaskBot`, `ErrorHandler`, `LogToFile`. |
| Action | `commandName` | e.g. `replace`, `runTask`, `try`, `logToFile`. |
| Enabled | `disabled` | boolean. |
| Configuration | `attributes` | list of `{name, value}` — §3.1. |
| Children | `children` | ordered child steps for container actions. |
| Branches | `branches` | alternative child collection (decision/loop bodies). |
| Return target | `returnTo` | `{ "type": "VARIABLE", "variableName": "<var>" }` — where the action stores its result. |

**Container actions** (`try`/`catch`/`finally`, `if`/`else`, `loop`) nest their
body in `children`; some also carry `branches` (observed on decision paths).
Exact `branches`-vs-`children` semantics per package is **`INFERRED`**.

### 3.1 Attribute values (`CONFIRMED` core; type set non-exhaustive)

An attribute is `{ "name": <str>, "value": <typed object> }`. The value object
carries a `type` plus a payload that depends on it:

| `value.type` | Payload key(s) | Example |
|--------------|----------------|---------|
| `STRING` | `string` (literal) **or** `expression` (contains `$var$` tokens) | `{"type":"STRING","expression":"$strTaskName.String:trim$"}` |
| `NUMBER` | `number` (string-encoded) | `{"type":"NUMBER","number":"-1"}` |
| `VARIABLE` | `variableName` | in `returnTo` |
| `TASKBOT` | `taskbotFile`, `taskbotInput` | sub-bot call — §3.2 |
| `DICTIONARY` | `dictionary`: `[{key, value}]` | `taskbotInput`, REST bodies |
| `LIST` | `list`: `[value, …]` | |
| `FILE` | `string` (often a `repository:///` or `file://` URI) | |
| `CREDENTIAL` | `credential`: `{lockerName, …}` | Vault reference — §4.3 |

`STRING` literal vs. `expression` is the key distinction for the "hard-coded
secret" and "unresolved variable" checks: a literal uses `string`, a
variable/expression uses `expression`. The full set of `type` tokens is
**`INFERRED`** (the list above is what this export exercised).

---

## 4. Variables (`CONFIRMED` object shape)

A variable object (confirmed keys):

```jsonc
{
  "name": "strTaskName",
  "type": "STRING",
  "description": "REQUIRED. …",     // free text; may be absent
  "readOnly": false,
  "input": true,                     // bot input
  "output": false,                   // bot output
  "defaultValue": { "type": "STRING", "string": "" }   // typed like an attribute value
}
```

`input`/`output` are independent booleans (a var can be neither = internal).
`defaultValue` is a typed value object (§3.1) and may be absent for some types.

### 4.1 Variable types (`OBSERVED` subset of an `INFERRED` set)

Confirmed present in this export: `STRING`, `NUMBER`, `DICTIONARY`, `LIST`,
`RECORD`. Also expected but **not yet seen here**: `BOOLEAN`, `DATETIME`, `FILE`,
`FOLDER`, `WINDOW`, `TABLE`, `CREDENTIAL`, `SESSION` (`INFERRED`). For `LIST`/
`DICTIONARY`/`RECORD`, how the element/field subtype is stored is **`UNKNOWN`**.

### 4.2 Variable references (`CONFIRMED`)

References appear inside `expression` strings as `$…$` tokens. Confirmed forms:

| Form | Example | Refers to |
|------|---------|-----------|
| plain | `$strBatch$` | the variable `strBatch` |
| type method | `$strTaskName.String:trim$` | `strTaskName`, transformed |
| record field | `$recRunConfig{sEnv}$` | field `sEnv` of record `recRunConfig` |
| global value | `$@Temp_Files$` | a Control Room **global**, not a bot var |
| namespace member | `$System:AATaskName$` | a system value, not a bot var |

The leading identifier is the variable name. `a360tools` extracts it with
`model.var_ref_names`, which **excludes** the global (`$@…$`) and namespace
(`$Ns:member$`) forms from the bot-variable set so the validator does not raise
false "undefined variable" findings. The token tail is a *structured* accessor
(`.method`, `:member`, `{field}`, `[index]`) and never spans whitespace/quotes —
this matters because attribute values can embed VBScript/PowerShell full of
unrelated `$`.

### 4.3 Credential references (`CONFIRMED` shape, `INFERRED` completeness)

A Vault reference appears as an attribute value `{"type":"CREDENTIAL","credential":{"lockerName":"…", …}}`.
`lockerName` is confirmed; the remaining keys (credential name, attribute name)
are **`INFERRED`** pending an export that exercises them fully.

---

## 5. Packages (`CONFIRMED`)

Each entry: `{ "name": <str>, "version": <str>, "settingsAttributes": [] }`.
Versions may carry a build suffix, e.g. `TaskBot 2.10.0-20241119-100739` or
`ErrorHandler 2.13.0-20241115-120032`. This is the dependency surface for
`11-dependency-analysis` and `15-change-impact-analysis`.

---

## 5b. Sub-bot ("Run task") calls (`CONFIRMED`)

A sub-bot call is a node with `packageName: "TaskBot"`, `commandName: "runTask"`,
and an attribute named `taskbot` whose value is:

```jsonc
{
  "type": "TASKBOT",
  "taskbotFile": { "type": "FILE", "string": "repository:///Automation%20Anywhere/Bots/…/Sub%20Worker" },
  "taskbotInput": { "type": "DICTIONARY", "dictionary": [ { "key": "…", "value": { … } } ] }
}
```

`taskbotFile.string` is a URL-encoded `repository:///` path to the called bot.
`a360tools deps` detects it and URL-decodes it so it matches the called bot's
stored path (and the export manifest's `scannedDependencies`) for graph building.

---

## 6. Known unknowns (confirm when an export exercises them)

- [ ] **Populated `triggers`** — the key exists but was empty in every bot seen;
      the trigger object shape is `UNKNOWN`.
- [ ] Full set of attribute `value.type` tokens and their payloads.
- [ ] `branches` vs `children` semantics per container package (If / Loop / Try).
- [ ] Full variable type-token set; element/field subtype storage for
      `LIST`/`DICTIONARY`/`RECORD`.
- [ ] Remaining `credential` object keys beyond `lockerName`.
- [ ] A360 **platform** version (distinct from `botCodeVersion`) and any
      cross-version differences in the above.

Each box checked with a citation to a real export is a promotion to `CONFIRMED`.
Keep this list honest.
