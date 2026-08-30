---
name: agent-workflow-engineering
description: Methodology for designing, building, and validating an AI-agent skill workflow — the design principles behind production workflow graphs (routing/evidence/synthesis/gates/recovery/knowledge loops), a 7-phase build loop with a pass/fail gate on every phase, and the anti-patterns that break workflows. Use when the user wants to build or restore a multi-skill agent workflow ("fill this workflow with skills", "build skills for this graph", "design an agent workflow"), or when asked how to systematically assemble and verify a skill system for a domain.
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [methodology, workflow, skills, design-principles, gap-filling]
    related_skills: [importing-external-skills, workflow-definition, workflow-runner, synthesize-project-context, engineering-closeout, project-context, parallel-feature-development]
---

# Agent Workflow Engineering

---

## Part I — Design Principles (what a workflow graph IS)

A production workflow is **not a collection of prompts**. It is a state machine: nodes are skills that transform state, edges carry artifacts/conditions/feedback, and the graph as a whole is an executable engineering object. A complete graph exhibits five node roles and seven layers.

### 1.1 The five node roles

Every node in a workflow graph plays one of these roles. When mapping or building a skill for a slot, ask which role the slot plays — the role dictates the required capability:

| Role | Function | Example slots |
|---|---|---|
| **Router** | Decides what happens next; costs nothing to run | S02 |
| **Context Builders** | Progressively increase the agent's state knowledge | S03, S05–S11 |
| **Executors** | Actually change the project | S12, S15 |
| **Coordinators / Validators** | Coordinate, verify, approve, release | S13, S14, S16, S17, S19 |
| **Knowledge Maintenance** | Ensure the project does not return to its prior knowledge state | S18, S20, S21, S22 |

### 1.2 The seven layers

```
1. INTAKE      — accept any input (request / idea / existing project)
2. UNDERSTAND  — clarify, fix, or confirm readiness
3. CONTEXT     — evidence → analysis (3 views) → synthesis into one project state
4. PLAN        — turn understanding into an executable plan
5. EXECUTE     — implement, identify parallel work, orchestrate, integrate
6. VERIFY      — hard gate (CI); failure loops back to EXECUTE
7. CLOSEOUT    — release if needed, audit, knowledge maintenance, archive
```

### 1.3 The design principles (each is a testable property)

When designing OR reviewing a workflow, check each property. A missing property is a defect.

1. **Intake is untyped** — the entry accepts request / idea / existing project alike; classification happens in the router, not at the door.
2. **The router is a cost controller** — a "change button color" task must not walk the full lifecycle. Routing by "what does this work need?" (clarify / fix / already-ready) is what keeps token cost proportional to task size. *Don't make agents re-pay for knowledge they already have.*
3. **Requirements must be structured** — a clarify node turns ambiguous human intent into a structured, consumable state (objective / constraints / acceptance criteria / scope / non-goals), because downstream nodes consume it.
4. **Evidence before understanding** — a source-evidence node extracts citable facts from the existing codebase before any analysis node runs. *Never let an agent understand a project from thin air* (evidence gating).
5. **Analysis is three orthogonal views** — architecture (what exists), dependencies (what constrains us), design (what should change). Three parallel analysis nodes fed by the same evidence; each answers one question.
6. **A synthesis hub creates the single source of truth** — all analysis + requirements + readiness converge into ONE project state before planning. Without it, planner A knows requirements, planner B knows architecture, and no agent holds the whole picture.
7. **Plan separates understanding from execution** — the plan node emits concrete tasks, dependencies, files to modify, order, acceptance criteria, and explicitly marks **parallelizable work** (this annotation is what triggers the sub-agent layer).
8. **Parallel work needs three nodes, not one** — identify (overview of parallelizable work) → orchestrate (controller with a feedback loop back to implementation: integration findings can require implementation updates = local recovery loop) → integrate (merge parallel streams, then hand to the gate). *The orchestrator's loop back is the recovery mechanism.*
9. **A hard gate is external to the agent** — CI (or equivalent) verifies what the agent claims. "Agent says done" is not done: failure loops back to implementation (execution-grounded recovery), success proceeds. *Self-reported completion is a hypothesis; the gate is the test.*
10. **Merge with a bypass** — after the gate passes, the merge node has two exits: closeout directly (small fixes, no release) or release → closeout. Release is optional, not a mandatory layer.
11. **Knowledge maintenance is an independent axis** — an audit node (zero in-degree, starts independently) maintains TWO knowledge streams: machine-facing (AGENTS.md: structure/commands/conventions/pitfalls) and human-facing (docs). The graph thereby improves itself: the next task starts from a better knowledge state (knowledge loop).
12. **Closeout is state archiving** — the terminal node records final status / changed files / tests / release state / docs state / remaining issues / next steps. It is a handoff contract, not "program exit".

### 1.4 Verification and recovery patterns

- **Local recovery loop**: integration feedback → implementation (bounded retry within a phase, not a full restart).
- **Execution-grounded recovery**: gate failure → implementation (the loop is driven by executed evidence, not self-assessment).
- **Knowledge loop**: audit → AGENTS.md/docs → closeout → next task starts richer.
- **Parallel knowledge loop**: audit runs concurrently with the main line, merging only at closeout.

---

## Part II — The Build Loop (7 phases)

### Phase 1 — Reconstruct the topology (before touching skills)

- Assign each node a **confidence grade** from visual evidence: visible text = high; inferred from position/topology = medium; pure guess = low. Document the grades.
- **Bind skills to topological function, not to guessed names** — "this slot is an analysis node fed by evidence, converging into a synthesis hub" survives a name correction; "this slot is called analyze-architecture" does not. Low-confidence names are mapping risks, not facts.
- **Gate**: topology is fully drawn (nodes, edges, labels, in/out degrees, independent-start nodes, multiple exits) and confidence grades are recorded, BEFORE any skill is chosen.

### Phase 2 — Map slots to skills (local first, then external)

1. Classify each slot by **node role** (Part I §1.1) — the role says what capability the skill must have.
2. Search the local library first (native + previously installed). Strong match = description covers the slot's semantics AND the skill's workflow satisfies the node's design property (e.g. a synthesis slot needs a convergence step, not just a file format).
3. For remaining slots, probe external registries by **semantic variants** (a hit on the exact name is a lead, not a match — batch-probe 4-6 variants per slot; e.g. analyze-dependencies / dependency-analysis / dependency-audit / dependency-scout all exist but mean different things).
4. **Read the body, not just the description.** Registry descriptions routinely look perfect while the body hides framework dependencies (MCP tools, `acfm`/`forge` CLIs, `~/.claude/` paths, slash-command ecosystems, `platforms:` claims). Grep for: `mcp__`, `.claude/`, `$ARGUMENTS`, `AskUserQuestion`, `agent__spawn`, `model:` frontmatter.
5. Record every rejection with its reason — the "name hit but wrong semantics" table saves the next search from re-probing.
6. Present candidates with sources and match grades (strong / partial / rejected-with-reason); the user decides the install set (strong-only vs including partials).
- **Gate**: every slot has a candidate or an explicit "no match, decision pending" — no silent holes.

### Phase 3 — Vet and fix before installing

For every install candidate:

- Frontmatter must have `name` + `description`. Registries sometimes omit `name` — add it, but **insert after the first `---`** (inserting before it breaks YAML parsing; verify with `skill_view`).
- Check internal `.md` links (registry copies often dangle — flag, don't fabricate), harness lock-in, license (single-file registries ship no LICENSE — note it; method-only content is low risk).
- **Language consistency is a quality gate**: mixed-language docs are a defect — pick one language per skill; if you rewrite any part, rewrite all parts you touch.
- **Generalize model-specific wording** ("Claude", "opus", "Haiku/sonnet") to "the assistant"; replace `$ARGUMENTS`-style variables and foreign slash commands with plain-language equivalents — they reference a harness that isn't yours.
- Fixes must be surgical and documented; do not silently rewrite an author's methodology.
- **Gate**: every installed skill passes frontmatter + no-harness + language-consistency checks (re-check ALL installed skills after the batch, not just the new ones).

### Phase 4 — End-to-end trial (the only way to find real gaps)

- Run the workflow on a REAL small task in a REAL project. Keep every artifact (each slot's output file) — they become the evidence base.
- Exercise the design properties from Part I: does evidence reach the analysis nodes? Does the synthesis hub actually converge? Does the gate's failure path loop back? Do skipped slots (per the graph's bypasses) behave?
- Record findings as numbered items with severity: **P0 gap** (a design property is unimplemented) / **skill tension** (two skills contradict — the trial is the arbiter; record the empirical verdict and its conditions) / **platform trap** (no skill covers it; domain knowledge caught it) / **repo issue** / **side effect** / **small pitfall** / **lucky catch**.
- **User corrections during the trial are data** — record them verbatim; they reveal the workflow's assumption errors.
- **Gate**: every slot executed is marked ✅ / ➖ (skipped by graph design) / 🔄 (loop in progress); the trial report lists findings, user corrections, and pending items.

### Phase 5 — Close gaps with evidence, not guesses

- A trial finding that matches a paper analysis upgrades it from hypothesis to confirmed — mark it so.
- For a missing capability, prefer a **minimal self-built skill** over adopting a heavy tool when the trial shows the minimal form suffices. Design it with: input/output contract, pass/fail gates, boundary rules (what belongs in other slots), batch interaction (per-item confirmation doesn't scale — measured), and anti-patterns.
- A self-built skill becomes canonical; later external duplicates get triaged against it.
- **Gate**: every P0/P1 finding has a resolution (self-built / adopted / explicitly accepted) before the workflow is declared closed.

### Phase 6 — Patch platform defects back into skills

- Trial findings about a skill's platform gap get patched into the skill itself, with the verified solution — the trial's working workaround IS the patch content.
- Re-verify after patching; mark the finding done in the record.
- **Gate**: each patched skill is re-read and confirmed (grep old pattern = zero hits).

### Phase 7 — Freeze the workflow as an executable graph

After the trial closes gaps and patches land, the workflow graduates from a mapping document to a first-class engineering artifact — a `workflow.yaml` written to the `workflow-definition` schema (mermaid-flavored: node blocks + ONE explicit `edges:` list; routing conditions, gate pass/fail, and feedback loops are edge properties, not hidden node fields):

- **Validate** with `validate-workflow.py` (11 gates: parse / required fields / node identity / edge integrity / cycle check / artifact closure / gate completeness / independent-axis / terminal / skill existence). A graph that fails validation must not run; the validator doubles as the CI gate.
- **Cycle design note**: only TWO kinds of dynamic back-edges are legal — `loop: true` (feedback/re-evaluation) and `kind: on_failure` (gate failure → implementation, execution-grounded recovery). An `on_failure` edge will trip a naive static cycle check (S16→S12 recovery loop) — exclude it from cycle detection deliberately, not as an afterthought.
- **Bundle a template copy** inside the definition skill (`templates/workflow.example.yaml`) so the graph survives the project directory; test scripts default to the bundled copy, never a project-absolute path (decoupling requirement).
- **Regression-test the validator** (1 positive + N negative crafted files) — the validator is the graph's unit test; re-run after ANY validator change.
- Execution is then driven by the `workflow-runner` protocol (topological schedule → per-node skill execution → artifact passing → gates/branches/loops/skips → `.workflow/state.json` persistence with checkpoint resume → bounded retry → closeout).
- **Gate**: `workflow.yaml` validates clean AND the validator's regression tests pass before the freeze is declared done.

---

## Part III — Anti-Patterns

- **Prompts instead of a state machine** — a flat list of prompts has no routing, no evidence, no gates; it is not a workflow.
- **Name hit ≠ semantic match** — always read the body; rejected near-misses are normal outcomes, not failed searches.
- **Description-only vetting** — the most framework-bound skills have the best descriptions.
- **Fabricating entries for missing artifacts** — mark `[MISSING]`, never invent.
- **Over-expanding** — after slots are filled and one trial ran, further searching has near-zero marginal value; stop and evaluate (self-build vs adopt vs accept) instead.
- **Counting errors** — registries dedupe silently; verify by `skill_view`, not directory counts; platform-filtered skills (`platforms:` excluding your OS) exist on disk but don't register.
- **Mandatory-release layers** — a release node with no bypass forces small fixes through a full release pipeline; the graph's bypasses are design, not shortcuts.
- **One giant synthesis node without a gate** — a hub that accepts everything becomes context rot; every synthesized entry needs an inclusion criterion.
- **Parallel without an integration contract** — parallel sub-agents without file-ownership and interface-contract rules produce merge chaos; file-set overlap is the serialization criterion (measured).
- **Losing the methodology in the results** — the deliverable is the loop plus its evidence, not the N skills. Write the record so the next domain doesn't restart from zero.
- **YAML frontmatter colon trap (self-built skills)** — an unquoted `description:` containing "word: word" fails parsing with "mapping values are not allowed". When a description contains colon+space, wrap it in quotes (`description: "..."`). Same class of fix as the registry `name:` quirk — verify every created skill with `skill_view`.

---

## Outputs

- A mapping document: slots → skills, node roles, match grades, install provenance, exclusions with reasons, confidence grades for nodes.
- The trial report: findings list (severity-graded), user corrections, gate results per slot, gap closures, pending items.
- The patched / self-built skills.
- The frozen executable graph: `workflow.yaml` + validator + regression tests + bundled template (Phase 7), executed via the `workflow-runner` protocol.
