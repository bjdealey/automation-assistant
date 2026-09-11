# knowledge/schema/

The working model of the A360 **bot JSON** schema — the single reference used by
JSON generation (`05`) and validation (`06`).

- **`a360-bot-json.md`** — the current working model. **Currently `INFERRED`**;
  it must be validated against real exports before it is relied upon.

As the schema is confirmed, add focused files (e.g. `node.md`, `variables.md`,
`attributes.md`, `packages.md`) and keep each field's confidence tag current.
When you confirm or correct a field, also update the matching `a360tools`
extractor and its test so code and knowledge stay in sync.

Rule: **never invent JSON fields.** A field that is not confirmed is marked
`INFERRED`/`UNKNOWN`, not presented as fact.
