---
name: synthesize-project-context
description: Synthesize upstream artifacts (requirements, source evidence, architecture/dependency/design findings, readiness) into candidate entries for PROJECT-CONTEXT.md — the S10 synthesis step that the project-context carrier format lacks. Use when multiple upstream analyses have completed and the unified project context must be written or updated (S10 synthesize-project-context slot), or when asked to "synthesize project context" / "update project context from findings" / "write the project context from these reports".
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [workflow, s10, context, synthesis]
    related_skills: [project-context, codebase-context, architecture-audit]
---

# Synthesize Project Context

## When to Use

- The S10 slot: after S03 (requirements), S05 (source evidence), S06 (architecture findings), S07 (dependency findings), S08 (design findings), S09 (readiness decision) outputs exist, before S11 planning.
- Any bulk update of `PROJECT-CONTEXT.md` from multiple findings (not single-entry adds — those go through `project-context add`).

## Inputs

- Paths to upstream artifacts (provided at invocation): requirements / source-evidence / architecture-findings / dependency-findings / design-findings / readiness-decision. Any subset is valid.
- Existing `PROJECT-CONTEXT.md` at repo root, if present.

## Outputs

- Updated `PROJECT-CONTEXT.md` (approved candidates appended to `## Active`).
- Synthesis summary: entries added / rejected (with reason) / merged with existing.

## Workflow

### Step 1 — Read upstream artifacts

Read every listed artifact fully. Missing files are marked `[MISSING]` in the summary — **do not fabricate entries for them**.

### Step 2 — Extract candidate entries (inclusion gate)

For each finding in each artifact, apply the gate. **PASS requires ALL four:**

- [ ] **Decision-relevant** — affects future agent decisions (not a one-off fact of the current task)
- [ ] **Durable** — still likely relevant in 90 days (the default expiry)
- [ ] **Non-duplicative** — not self-evident from code, README, or AGENTS.md
- [ ] **Safe** — not a secret, credential, or .env content

Any failure → REJECT, and record the reason in the summary (transparency, not silence). When in doubt, reject: the cost of a stale entry is paid by every future session that reads it.

### Step 3 — Deduplicate and boundary-check

1. Read existing `## Active` entries of `PROJECT-CONTEXT.md`; absorb candidates that restate an existing fact (merge, don't duplicate).
2. Boundary rules — content that belongs elsewhere is excluded here:
   - Rules, commands, conventions → `AGENTS.md` (S20)
   - Formal documentation → `docs/` (S21)
   - Long-term decisions with rationale → decision records (e.g. `decision-memory` skill / ADRs)
   - This file holds **informal but decision-relevant project knowledge**: gotchas, half-finished state, historical constraints, warnings.
3. For each surviving candidate assign: **source** (which artifact), **scope** (`global` | module/area name), **expiry** (default 90 days from today; `never` only for conventions that must not expire).

### Step 4 — Batch confirm

Present ALL candidates at once as a table:

| # | Candidate entry | Source | Scope | Expiry |
|---|---|---|---|---|

Ask once: approve all / adjust (specify rows) / reject (specify rows). **Do NOT run `project-context add` per entry for bulk synthesis** — its per-entry confirmation flow does not scale (measured in trial F1).

### Step 5 — Append

Write approved entries into `## Active` of `PROJECT-CONTEXT.md` (create the file with the standard header if absent). Follow the exact entry format from the `project-context` skill.

### Step 6 — Verify (completion gate)

Before declaring done, all must hold:

- [ ] Every entry has source, scope, and expiry
- [ ] No duplicates with existing Active entries
- [ ] No entry duplicates AGENTS.md / docs content
- [ ] Active count within the 50-entry / ~200-line cap (warn if approaching; suggest `project-context cleanup`)

## Anti-Patterns

- **Extracting everything** — the gate exists to prevent context rot; a bloated file gets ignored.
- **Per-entry confirmation for bulk synthesis** — batch confirm once, adjust by row.
- **Writing rules/commands** — belongs in AGENTS.md, not the context file.
- **Fabricating entries for missing artifacts** — mark `[MISSING]` and move on.
- **Skipping expiry** — default 90 days; `never` requires explicit justification.
- **Duplicating an existing Active entry** — merge or reject; duplicates halve the file's signal.
