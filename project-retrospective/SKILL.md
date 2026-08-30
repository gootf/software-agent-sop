---
name: project-retrospective
description: Use when a project needs multi-session retrospective analysis — after milestones, before starting a new phase, when vision drift is suspected, or every 3-5 sessions. Triggers: user says "retro", "run a retro", "since-last-retro"; asks to analyze patterns, recurring mistakes, or correction trends across multiple sessions; says "how did we get here" or "project history" in a project-arc context (not single-file diffs or README edits); or notes that project memory has drifted from what actually happened across sessions. NOT for: single-session review, memory cleanup, retro templates, or git-level file diffs.
argument-hint: [full | since-last-retro | last-N]
---

# Project Retrospective

> **Hermes adaptation** of the claudskills.com community skill (same name). Four
> portability changes, methodology unchanged: (1) session source is the Hermes
> session store (`session_search`) instead of `~/.claude/exports/`; (2) historian
> dispatch uses Hermes `delegate_task` instead of the Claude Code `Agent` tool;
> (3) rules/memory targets are Hermes-native (project memory files, the `memory`
> tool, skills) instead of `~/.claude/rules/`; (4) all model-specific wording
> ("Claude", "opus", "Haiku/sonnet") is generalized to "the assistant".

Analyze a project's session history by dispatching parallel historian agents to read each session record, then synthesizing their findings into a structured analysis document. The value is in the **extraction criteria** — domain-specific signals, not generic summarization.

## Modes

Two modes, differentiated by **output format** (not historian cost):

| Mode | Output | When to Use |
|------|--------|-------------|
| **full** | Standalone ANALYSIS (superset, safe to delete prior) | Phase transitions, major incidents, no prior retro exists, reset the chain |
| **incremental** | Delta UPDATE (references prior retro, never delete prior) | Periodic check-ins (every 3-5 sessions), ongoing projects with an existing retro baseline |

Both modes reuse prior historian work when a prior retro exists — only NEW session records get fresh historians. The difference is what the synthesizer produces: a standalone document vs. a delta document.

## Arguments

The mode/scope argument comes from the user's request wording: "full", "since-last-retro", or "last-N" (e.g. "retro last 5"). If the user gives no argument, apply the context-aware default below.

| Argument | Behavior |
|----------|----------|
| *(none)* | **Context-aware default.** Check for prior retros first (Phase 1.5). If a prior retro exists, default to **incremental**. If no prior retro exists, default to **full**. |
| `full` | **Explicit full mode.** User override — produce a standalone ANALYSIS. Still reuse prior historian work (only dispatch historians for new session records). |
| `since-last-retro` | **Explicit incremental mode.** Produce a delta UPDATE against the prior retro. |
| `last-N` | **Full mode** scoped to the N most recent session records only. Always dispatches fresh historians for all N session records — does not reuse prior retro content. Skip Phase 1.5 entirely. Use for focused recent-session analysis. |

If the argument doesn't match any of the above, echo it back and ask what was meant.

**User override is final.** If the user explicitly says `full`, produce a full ANALYSIS — don't argue or suggest incremental. The context-aware default only applies when no argument is given.

## Phase 1: Discover & Validate Session Records

Obtain Hermes session records (first available wins):

1. **`session_search` retrieval** — query the session store by project keywords; take the full message text of each relevant session as one record block, sorted by date.
2. **User-provided exports** — if the user supplies session export files (.txt/.md), read those.
3. **Hermes CLI export** — if a `hermes sessions`-style command can dump session text, use it; otherwise fall back to option 1.

If `last-N` was provided, take only the last N records.

**No session records available:** Stop immediately. Report the issue and suggest confirming that session history exists (Hermes records sessions automatically in the local store; search by project name or keywords). Do NOT proceed with zero records.

**Some records missing:** List what was found, proceed with available records, and note gaps in the final output.

## Phase 1.5: Detect Prior Retro

In both modes, find the most recent full retro document:
```
docs/retros/*-PROJECT-HISTORY-ANALYSIS.md
```

**Fallback for pre-v2 projects:** If `docs/retros/` has no matches, also check `docs/*-PROJECT-HISTORY-ANALYSIS.md` (pre-v2 output path). If found there, move it to `docs/retros/` first, then proceed.

**If no prior retro exists anywhere:**
- **Incremental mode:** Report this and switch to full mode automatically. Incremental requires a baseline.
- **Full mode:** Proceed normally — all session records need fresh historians.

**If prior retro found:**
1. Read it fully — it contains the synthesized analysis of previously-analyzed sessions.
2. Extract the session range it covers (from the `**Sessions:** <range>` header line).
3. Determine which session records are NEW (not covered by the prior retro's session range).
4. If zero new session records exist since the prior retro: report "nothing new to analyze — prior retro is current" and stop. This applies to both modes — re-synthesizing the same data produces equivalent output.
5. **Full mode:** The prior retro's content serves as pre-computed extraction for already-analyzed sessions (see Phase 2).

**Chaining semantics:** Incremental always chains from the last *full* retro (ANALYSIS file), never from a prior *incremental update* (UPDATE file). This means multiple incremental updates can accumulate between full retros. Each delta is independently interpretable against the same baseline. To reset the chain, run a full retro.

**Gaps in prior retro:** If the prior full retro noted missing session records (sessions it couldn't analyze), those gaps are permanent unless a new full retro is run. Incremental mode does not backfill gaps — it only analyzes session records newer than the prior retro's session range.

## Phase 2: Spawn Historians (Parallel Background Agents)

**Incremental mode:** Launch one background agent per NEW session record only.

**Full mode with prior retro (Phase 1.5 found one):** Only dispatch historians for session records NOT covered by the prior retro. The prior retro's content serves as pre-computed extraction for already-analyzed sessions — pass it to the synthesizer in Phase 3 alongside the new historian reports. This gives full-mode superset output with incremental historian cost.

**Full mode without prior retro:** Launch one background agent per session record (all session records).

Dispatch each historian with Hermes `delegate_task` (runs in the background by default; one sub-agent per session record):

```
delegate_task(
  goal: "Historian: {SESSION_LABEL} — analyze the session record below per the extraction template; return clean markdown text only, write no files",
  context: "<full extraction template> + <session record text (contents of {FILE_PATH})>"
)
```

**Model selection:** Hermes sub-agents inherit the parent model. Session records can be long (30-65K tokens) — if the parent model is weak, extraction quality will drop; configure a stronger model for historians in the delegation settings if needed.

**Collection:** After ALL historians complete, collect their reports and proceed to Phase 3 (for 15+ reports, delegate the synthesis itself to a dedicated sub-agent — see Phase 3).

### Historian Extraction Template

Each historian receives this prompt with `{FILE_PATH}` and `{SESSION_LABEL}` filled in:

```
Read the COMPLETE session record at {FILE_PATH}. This is a Hermes session
record from {SESSION_LABEL}.

Session records contain the visible conversation: user messages, assistant
responses, decisions, corrections, and deliverables. Tool calls may be
collapsed or truncated — sub-agent prompts, memory writes, and sub-agent
details may be behind expansions and NOT visible.
Extract what IS visible: user messages, assistant responses, decisions,
corrections, and deliverables.

Extract the following. Include brief quotes or concrete references — not
vague summaries.

1. **How session started**: First user prompt. Continuation or fresh?
   How was context established?
2. **Original intent vs actual**: What was planned vs what happened.
   Why different?
3. **Key decisions**: Technology, architecture, process decisions — with
   rationale and whether they held or were reversed.
4. **User corrections**: Every time the user caught the assistant making a
   mistake. QUOTE the correction verbatim. This is the most valuable
   data — pattern these by type.
5. **Mistakes and anti-patterns**: What went wrong, root causes,
   systemic issues (not just one-offs).
6. **Quality moments**: When user pushed for higher rigor — what was
   the ask and what was the assistant's response?
7. **Roadmap evolution**: How did the plan/scope change during the session?
8. **Deliverables**: Files created/modified, PRs opened/merged/closed,
   documents produced.
9. **Handoff**: What was stated as the next session's task? Deferred items?

Output as clean markdown. No preamble. Return TEXT DATA only — do NOT
write any files.
```

**Historian failure:** Relaunch once. If it fails again, proceed with available reports and note the gap. Do NOT approximate from other historians or from project memory — relaunch, don't guess.

## Phase 3: Synthesize

After ALL historians complete, combine reports into a single analysis.

**Synthesizer delegation:** If fewer than ~15 historian reports, the orchestrator can synthesize inline. For 15+ reports, delegate to a dedicated synthesizer sub-agent (strongest model accessible) — the combined reports plus prior retro content may exceed comfortable inline processing. Pass all historian reports and (if applicable) the prior retro content in the synthesizer's prompt.

**Full mode** uses the Full Synthesis Template. **Incremental mode** uses the Incremental Synthesis Template.

**Full mode with prior retro input:** The synthesizer needs BOTH the new historian reports AND the prior retro content. The prior retro provides the deep extraction for already-analyzed sessions; the new historian reports cover the delta. The synthesizer must treat both as equal primary sources and produce a standalone superset ANALYSIS — not a delta, not a summary of the prior retro with new sections appended. Re-synthesize the full narrative from all available data.

**Incremental mode input:** The synthesizer needs BOTH the new historian reports AND the prior retro content (read in Phase 1.5). If delegating synthesis to a sub-agent, include the prior retro text in its prompt — the sub-agent doesn't have Phase 1.5 context.

### Full Synthesis Template

```markdown
# {Project Name} — Project History Analysis

**Generated:** YYYY-MM-DD HH:MM UTC | **Sessions:** range | **Agents:** N+1

## 1. Original Vision vs Current State
The user's original vision, how it evolved, honest drift assessment —
were changes justified or accidental?

## 2. Roadmap: Original vs Actual
| Session | Planned | Actual | Deviation Justified? |

## 3. Decision Log
| Session | Decision | Rationale | Status (held/reversed/superseded) |

## 4. Mistakes and Corrections
Pattern mistakes by type. Common assistant behavioral patterns to seed:
- Deferral disguised as process (effort avoidance)
- Overconfidence without verification (asserting not checking)
- Not following own rules (loaded but not consulted)
- Fabricated/unverified claims (training data biases)
Also surface any project-specific patterns beyond these.
Count instances per pattern — reveals systemic issues.

## 5. User Teaching Moments
Recurring lessons the user had to teach. These are the user's priorities
and standards — future sessions must internalize them.

## 6. What's Valid Now
Current state: artifacts, what's on main, what's pending. Clear inventory.

## 7. Recommended Next Step
Justified from FULL history, not just the latest project memory. If history
suggests a different priority than project memory, say so.
```

### Incremental Synthesis Template

```markdown
# {Project Name} — Project History Update

**Generated:** YYYY-MM-DD HH:MM UTC | **New sessions:** range | **Prior baseline:** prior-retro-filename
**Cumulative sessions:** full-range | **Agents:** N+1

## Prior Retro Summary
One-paragraph summary of what the prior retro established as the
project state, key patterns, and outstanding issues.

## 1. What Changed Since Last Retro
New decisions, direction shifts, scope changes in the delta sessions.
Reference prior retro for context where relevant.

## 2. New Decisions
| Session | Decision | Rationale | Status |

## 3. Correction Pattern Update
Carry forward the prior retro's correction patterns. For each pattern:
- Prior count + new count = cumulative total
- Trend: improving / stable / worsening (compare per-session rate)
- Any NEW patterns not in the prior retro get their own entry.

## 4. New Teaching Moments
Lessons from new sessions only. Note which are genuinely new vs
reinforcement of prior patterns.

## 5. Current State & New Deliverables
Updated inventory: what's on main, what's pending, what changed.
List files created/modified, PRs merged, documents produced in new sessions.

## 6. Recommended Next Step
Justified from cumulative history (prior retro + new sessions).
```

**Cross-session deduplication:** A decision in S1 referenced in S3 appears once with both session numbers.

## Phase 4: Write & Integrate

### Write the analysis

Output to the retros directory (create if needed):

**Full mode:** `docs/retros/YYYY-MM-DD-PROJECT-HISTORY-ANALYSIS.md`
**Incremental mode:** `docs/retros/YYYY-MM-DD-PROJECT-HISTORY-UPDATE.md`

### Update project memory

1. Add a reference to the retrospective document.
2. Evaluate whether findings warrant new rules or memory:
   - Project-specific lessons → project memory file (e.g. `.hermes.md`) or PROJECT-CONTEXT.md
   - General patterns (cross-project) → update the relevant Hermes skill or global memory (`memory` tool)
   - Existing-rule violations → note the enforcement gap, don't duplicate
3. Threshold: happened twice, or high-severity once.

### Commit

Commit the analysis and any memory updates.

## Deletion Semantics

| Mode | Prior retro safe to delete? | Why |
|------|-----------------------------|-----|
| **Full** | Yes | Full output is a superset — contains everything the prior retro had plus more. Prior becomes redundant. |
| **Incremental** | **Never** | Incremental output is a delta — it references and builds on the prior retro. Deleting the prior loses the deep extraction from earlier sessions permanently. The chain of incremental retros forms a linked history. |

## Anti-Patterns

- **Single agent for all records** — each agent needs full context for one session record. Combining loses depth.
- **Compressing historian reports** — the synthesizer needs full detail for cross-session patterns.
- **Skipping "User corrections"** — the most valuable signal. Without it, the retro is generic.
- **Writing from memory files only** — project memory is derivative. Session records are the primary source.
- **Serial processing of all records** — historians must run in parallel (one background sub-agent per record); sequential runs lose the parallelism the design depends on.
- **Weak model for historians** — session records are long (50-200KB scale); weak models miss nuance. Use the strongest model available.
- **Summarizing instead of extracting** — "summarize the session" produces generic output. The 9-point extraction template IS the skill's value.
- **Re-analyzing old sessions in incremental mode** — the whole point of incremental is O(delta). If you're spawning historians for sessions the prior retro already covers, you're doing it wrong.
- **Fresh historians for already-extracted sessions** — if a prior retro exists, its content IS the extraction for those sessions. Dispatching new historians to re-read the same session records wastes sub-agents and produces equivalent output. Only dispatch historians for sessions the prior retro doesn't cover.
- **Hardcoding default mode without checking project state** — the default (no argument) should check whether prior retros exist before committing to full or incremental. A blind default ignores available information.
- **Deleting prior retro after incremental** — incremental output is a delta, not a superset. The chain breaks.
- **Running incremental without a baseline** — if no prior retro exists, switch to full mode. Don't produce a delta with nothing to delta against.
