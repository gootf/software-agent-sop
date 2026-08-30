---
name: delegation-protocol
description: Structured 6-section delegation template and session-continuity rules for orchestrating sub-agents. Load before spawning any agent.
---
You are delegating work to a sub-agent. The sub-agent has not seen the codebase or the conversation — your prompt IS its entire context. Treat delegation as writing a contract: explicit, scoped, and verifiable.

## The 6-section template (every delegation)

Every delegation prompt MUST include all six sections. Vague prompts produce vague results and waste tokens on re-exploration the orchestrator already did.

```
## TASK
[One atomic goal. One verb. One outcome. No "and also".]

## EXPECTED OUTCOME
[Concrete deliverables and success criteria. "I will know this is done when ..."]

## REQUIRED TOOLS
[Explicit allowlist: fs_read, fs_grep, etc. Prevents tool sprawl.]

## MUST DO
[Exhaustive requirements. Leave nothing implicit. If you'd be annoyed by the agent not doing X, list X.]

## MUST NOT DO
[Forbidden actions. Anticipate rogue behavior. "Do not modify files outside src/auth/."]

## CONTEXT
[File paths, code snippets, existing patterns, constraints. Paste actual code lines from prior exploration — not just file paths.]
```

## Session continuity (NON-NEGOTIABLE)

Every delegation result includes a session_id. **Use it.**

- Task failed/incomplete → resume with `session_id` + a tight "Fix: <error>" prompt.
- Follow-up on a result → resume with `session_id` + "Also: <question>".
- Multi-turn with the same agent → always resume. Never start fresh.

Starting a fresh agent for a follow-up forces it to re-read every file it already read. That's 70%+ wasted tokens, plus the agent loses the reasoning it built up.

After every delegation, **store the session_id** for potential continuation.

## Skill nudges to delegates

Sub-agents have their own skills. Nudge them in the CONTEXT section:

> "Load `code-review` before evaluating the diff."
> "Load `frontend-ui-ux` before editing component files."
> "Load `git-master` before touching history."

A one-line nudge saves the delegate a skills-catalog lookup turn.

## Verification after delegation

A delegation is NOT complete when the sub-agent returns. It is complete when YOU have verified:

1. Did it work as expected? (Did the file change? Did the test pass?)
2. Did it follow existing codebase patterns?
3. Did the EXPECTED OUTCOME actually materialize?
4. Did it respect MUST DO and MUST NOT DO?

If any answer is no → resume the session with a corrective prompt. Do not re-spawn from scratch.

## Parallel dispatch decision rule

Dispatch multiple implementers in parallel ONLY when both conditions hold:
their file sets are disjoint, AND a shared contract is already frozen
(types, function signatures, message shapes, defaults). Otherwise run
sequentially — shared files or an unfrozen contract are exactly how parallel
tracks collide.

- **Freeze the contract first**: one serial task defines the interface;
  parallel tasks consume it read-only. Never let two agents edit the same file.
- **Enforce disjointness via MUST NOT DO**: each task's forbidden list names
  the other tracks' files. That turns "disjoint" from an assumption into a
  checkable constraint.
- **Verification while tracks run**: per-track `tsc`/tests will transiently
  fail on siblings' half-written files (mid-edit snapshots). Verify against
  the track's own files and tell each agent the sibling errors are not its
  concern; defer full-suite verification to the integration point.
- **Integration is a separate step**: after all tracks report, run the full
  suite (lint/typecheck/test/build), review the combined diff, and fix
  residuals yourself. Never dispatch fix requests back mid-integration.
- Note: this complements `subagent-driven-development`'s "never parallel"
  rule — that rule assumes tasks share the codebase; the exception here is
  strictly file-disjoint tracks under a frozen contract.

## Anti-patterns

- "Follow existing patterns" with no snippet → agent guesses, often wrong
- Multi-goal prompts → agent does the easy one, skips the rest
- Missing MUST NOT DO → agent over-reaches into unrelated files
- Discarding session_id on failure → forced re-exploration, wasted tokens
- Re-spawning instead of resuming for a 1-line fix → 10x cost
