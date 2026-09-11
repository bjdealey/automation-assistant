# knowledge/platform/

A360 **platform** behaviour: the Control Room UI, bot editor, packages and
actions, variables, triggers, deployment, run configuration, logging, and
runtime semantics.

Keep this **free of organisation-specific examples** — those go in
`../organisation/` or `../bots/`. This folder is about how A360 *itself*
behaves.

**Every entry uses the template in `../README.md` and carries a source +
confidence tag.** Prefer `CONFIRMED` (docs + version, or observed UI/export);
mark anything else honestly.

Suggested files as knowledge accrues:
- `packages/<package>.md` — actions in a package, their fields, JSON mapping.
- `variables.md` — variable types and their runtime semantics.
- `triggers.md` — trigger types and configuration.
- `deployment.md` — deploy, run config, versioning, export/import behaviour.
- `runtime.md` — execution order, error propagation, session handling.
