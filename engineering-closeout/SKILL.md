---
name: engineering-closeout
description: Produce the engineering closeout report for a completed work unit — final status, changed files, tests, release state, docs state, remaining issues, next steps — with a completion gate. Use when implementation and verification are done and the work must be formally closed (S22 project-closeout slot), or when asked to "close out", "wrap up the project", "write the closeout", "summarize what was done". Complements project-retrospective (which analyzes multi-session history); this skill captures the current work unit's engineering state.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [workflow, s22, closeout]
    related_skills: [project-retrospective, release-management, architecture-audit]
---

# Engineering Closeout

## When to Use

- The S22 slot: after implementation, integration, and verification complete (S12–S17), before handing the project back to the user or starting the next work unit.
- User says "close out", "wrap up", "summarize the project state".

## Inputs

- Changed-file list, test results, CI status, release state, docs state, remaining issues — gathered from the work just performed (git status/diff, test/CI output, PR state, docs touched).

## Outputs

- A closeout report with the seven sections below, written to the project (e.g. `docs/closeout-YYYY-MM-DD.md`) or returned inline if the user prefers.

## Report Structure

```markdown
# <Work unit> — Closeout Report

> Date: <date> · Project: <name> · Scope: <what was done, one line>

## 1. Final Status
What the work delivered (features/fixes/behavior), stated concretely.

## 2. Changed Files
Explicit list: source files, configs, docs, new files (e.g. tests/, CI config).

## 3. Tests
- New tests written: <count and what they cover>
- Existing suite: <pass/fail summary>
- Lint / typecheck / build: <per-tool status>

## 4. Release State
- Released / not released (and why — e.g. no release needed, per workflow path)
- Version: <current version, bump if any>

## 5. Docs State
- README / help text / design docs: <synced / pending items>
- AGENTS.md / PROJECT-CONTEXT.md: <created/updated>

## 6. Remaining Issues
Numbered list of known issues, each with who owns it (user verification, follow-up task, accepted).

## 7. Next Steps
Concrete next actions, ordered (e.g. CI green → merge PR → delete branch).
```

## Completion Gate

Before declaring the closeout complete, ALL must hold:

- [ ] Every section has substantive content — no empty sections, no "N/A" as a placeholder (write "not needed, because…" if applicable)
- [ ] Tests / CI state is explicit: passed / failed / pending — never implied
- [ ] Remaining Issues lists every known gap (a closeout that claims completion with unresolved known issues is incomplete)
- [ ] Next Steps are actionable and ordered
- [ ] The report distinguishes verified facts from assumptions (e.g. "CI passed" vs "manual browser check pending user")

If any fails, complete the missing section before delivering — a closeout is the handoff contract for the next session/user.

## Anti-Patterns

- **Empty sections** — an "N/A" section hides missing information; state why it doesn't apply.
- **Vague test status** — "tests are fine" is not a status; give counts and per-tool results.
- **Hiding remaining issues** — known issues belong in section 6, not omitted; omission is how they get lost.
- **Unordered next steps** — dependencies between steps must be visible (e.g. CI before merge).
- **Confusing verified with assumed** — mark user-side verification (manual browser checks, deployment approval) as pending, not done.
- **Duplicating project-retrospective** — this report captures current state; historical analysis belongs to the retro skill.
