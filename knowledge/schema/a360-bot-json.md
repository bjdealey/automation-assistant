# A360 bot JSON — working model

> **Confidence for this whole document: `INFERRED`.**
> It is a *starting hypothesis* assembled from general knowledge of Automation
> Anywhere A360, **not** validated against your environment. Field names,
> nesting, and allowed values **must be confirmed against real exported bots**
> from your control room before any of it is treated as fact. Where a claim is
> corrected by a real export, change its tag to `CONFIRMED`, cite the export,
> and update `a360tools` + its tests to match.
>
> **A360 version / environment:** unknown — record it here once known.

The purpose of this file is to be *wrong in known places* rather than
confidently vague: it gives the copilot and the tools a shape to look for, and a
checklist for validating that shape.

---

## 1. How to obtain ground truth (do this first)

1. In the A360 Control Room, build (or open) a small bot with one of each
   construct you care about: an assignment, an If, a Loop, a Try/Catch, a
   message box, a "Run task" (sub-bot) call, and one input + one output
   variable.
2. Export the bot (or copy it from a Git-backed repository if your Control Room
   is Git-integrated).
3. Open the `.bot` file — it is JSON. Save a copy under `knowledge/bots/` and
   run `python -m a360tools normalize <file>` to get a stable, readable form.
4. Compare the real structure against §2–§5 below and correct them. Each
   correction is a `CONFIRMED` knowledge gain.

**GUI → stored representation → JSON → runtime** is the mapping we are building.
For each UI action, capture: the human name, its package, its required/optional
fields, their data types and allowed values, and how each appears in JSON.

---

## 2. File & top-level shape (`INFERRED`)

- A `.bot` file is a single JSON object (UTF-8).
- Expect (names to be verified) something equivalent to:
  - a **node tree / list** describing the ordered steps of the task;
  - a **variables** collection;
  - a **package dependency** list (package name + version);
  - **metadata** (schema/format version, bot uid, name).

```jsonc
// SHAPE HYPOTHESIS — verify every key name against a real export.
{
  "nodes":    [ /* ordered task steps — see §3 */ ],
  "variables":[ /* see §4 */ ],
  "packages": [ /* see §5 */ ],
  "metadata": { /* bot uid, name, schema/format version — names TBD */ }
}
```

> Do **not** emit JSON in this shape to a Control Room as if it were valid. It is
> a hypothesis for *analysis*, not a `CONFIRMED` generation target.

---

## 3. Nodes / steps (`INFERRED`)

Each step in the task is expected to be an object carrying at least:

| Concept | Likely JSON role | Notes |
|---------|------------------|-------|
| Which package | e.g. `packageName` | The action's package (e.g. Excel, String, Loop). Verify key. |
| Which action  | e.g. `commandName` | The specific command within the package. Verify key. |
| Configuration | e.g. `attributes` (list of `{name, value}`) | The fields shown in the UI action editor. Verify shape. |
| Identity      | e.g. `uid` | Stable id used for references / ordering. Verify. |
| Children      | e.g. `branches` / nested `nodes` | Container actions (If, Loop, Try) hold child steps. Verify. |

**Container actions** (If / Else If / Else, Loop, Try / Catch / Finally) nest
their body steps. The exact representation of branches (e.g. a `branches` array
vs. typed child collections) is **UNKNOWN** until verified.

**Attribute values** are expected to be typed objects (a literal, a variable
reference, or an expression), not bare scalars. Capturing the difference between
*literal*, *variable reference*, and *expression* is high value — record real
examples of each.

---

## 4. Variables (`INFERRED`)

A variable is expected to carry: a **name**, a **type**, a **default/initial
value**, and **input/output** flags (whether it is a bot input, a bot output, or
internal).

### 4.1 Variable types — hypothesis list

These type names are commonly associated with A360; treat as `INFERRED` until an
export confirms the exact tokens:

`STRING`, `NUMBER`, `BOOLEAN`, `DATETIME`, `LIST`, `DICTIONARY`, `RECORD`,
`FILE`, `FOLDER`, `WINDOW`, `TABLE`, `CREDENTIAL`, `SESSION`.

For each, we still need to confirm: the exact token, how the default value is
represented, and (for `LIST`/`DICTIONARY`) how the element/subtype is stored.

### 4.2 Variable references

How a step refers to a variable (e.g. a `$variableName$` expression token vs. a
structured reference object) is **one of the most important things to confirm**,
because generation and the "unresolved variable" validation check both depend on
it. Record real examples verbatim.

---

## 5. Packages (`INFERRED`)

- A bot declares the **packages** it uses, each with a **name** and a
  **version**. This is the dependency surface that must exist in the target
  Control Room for the bot to run.
- Version pinning matters: a bot built against one package version may behave
  differently (or fail to import) against another. This feeds
  `11-dependency-analysis` and `15-change-impact-analysis`.

---

## 6. Known unknowns (things to confirm early)

- [ ] Exact top-level key names and the schema/format version field.
- [ ] Node object: exact keys for package, command, attributes, uid, children.
- [ ] Representation of container branches (If / Loop / Try).
- [ ] Attribute value typing: literal vs. variable vs. expression.
- [ ] Variable object keys; exact type tokens; default-value representation.
- [ ] Variable reference syntax inside attributes.
- [ ] Sub-bot ("Run task") call: how the target bot path/uid is stored.
- [ ] Credential references (Credential Vault): how attributes point at them.
- [ ] Trigger representation (if triggers live in the bot file at all).
- [ ] Differences across A360 versions in any of the above.

Each box checked with a citation to a real export is a promotion from
`INFERRED` to `CONFIRMED`. Keep this list honest.
