---
name: 15-change-impact-analysis
description: Assess the blast radius and risk of a proposed change to an A360 bot or shared component before it is made. Use when deciding whether a change is safe, what it could break, or what must be re-tested — especially for shared sub-bots, changed variable contracts, or package version changes. Combines the dependency graph (11) with a structural diff to identify affected consumers and regression risks.
---

# 15 · Change-impact analysis

**Goal:** know what a change could break before making it.

## When to use

- Before editing a **shared** sub-bot or component.
- Before changing a bot's **variable contract** (inputs/outputs), or a **package
  version**.
- To scope re-testing for any non-trivial change.

## Method

1. **Define the change** precisely (what will differ). If you have both
   versions, get the structural diff:
   ```bash
   cd tools
   python -m a360tools diff <old_bot> <new_bot>
   ```
2. **Map dependencies** (`11-dependency-analysis`), especially the **reverse**
   "used-by" set: which bots call this component?
3. **Trace the change through consumers:**
   - Changed input/output variable → every caller that passes/consumes it.
   - Changed behaviour/side effect → every workflow relying on the old behaviour.
   - Changed package version → every action from that package; portability.
   - Changed file/credential/system usage → environment + permissions impact.
4. **Assess regression risk** per affected consumer (HIGH/MEDIUM/LOW).
5. **Define the validation set** (`12-testing`) — the minimum tests to prove the
   change is safe across consumers.

## Output

- **Blast radius:** the set of affected bots/components/systems.
- **Risks:** ranked, with the failure mode for each.
- **Recommended validation:** the tests to run before/after.
- **Go / caution / no-go** recommendation with reasoning.

## Guardrail

If the reverse-dependency set can't be fully determined (corpus incomplete, or
sub-bot references still `INFERRED` in the schema), say the blast radius is a
lower bound, not complete.
