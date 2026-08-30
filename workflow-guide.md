# The Consolidated AI-Agent Workflow (22-Slot SOP) — Guide

> Version: workflow.yaml v1.0.0 (22 nodes / 33 edges)
> Core assets: `workflow.yaml` (this directory) + the `workflow-definition` / `workflow-runner` / `agent-workflow-engineering` skills (shipped as directories in this repository)

---

## 1. What This Is

A 22-node software-engineering agent SOP graph, solidified into an **executable graph definition**:

- **Graph (structure)**: `workflow.yaml` — nodes + explicit edges (order/dependency/condition defined before execution)
- **Nodes (content)**: 22 independent skills — each node is an executable unit, strictly decoupled from the graph
- **Validation (tests)**: the `validate-workflow.py` script in `workflow-definition` — 11 gates, CI-runnable
- **Execution (scheduling)**: `workflow-runner` — topological order, artifact passing, gates/branches/loops, state persistence with checkpoint recovery

## 2. The Full Graph (mermaid)

```mermaid
flowchart TB

%% =========================================================
%% Phase 0 — Intake / Routing
%% =========================================================

S01["S01<br/>task-intake<br/><br/>request / idea / existing project"]

S02{"S02<br/>ask-matt<br/><br/>what does this work need?"}

S03["S03<br/>interview-me<br/><br/>clarify requirements"]

S04["S04<br/>diagnosing-bugs<br/><br/>fix existing issues"]

S05["S05<br/>codebase-context<br/><br/>extract source evidence"]

S09["S09<br/>check-readiness<br/><br/>context already sufficient"]


S01 --> S02

S02 -->|"requirements are unclear"| S03

S02 -->|"existing issue or bug needs fixing"| S04

S02 -->|"project context is already sufficient"| S09

S04 -.->|"return for re-evaluation<br/>loop"| S01



%% =========================================================
%% Phase 1 — Context / Analysis / Planning
%% =========================================================

S06["S06<br/>analyze-architecture"]

S07["S07<br/>environment-discovery<br/><br/>dependency analysis"]

S08["S08<br/>solution-architecture<br/><br/>system design"]

S10["S10<br/>synthesize-project-context<br/><br/>PROJECT-CONTEXT.md"]

S11["S11<br/>planning-and-task-breakdown"]


S03 -->|"clarified requirements"| S06

S03 -->|"clarified requirements"| S07

S03 -->|"clarified requirements"| S08

S03 -->|"clarified requirements"| S10


S05 -->|"source evidence"| S06

S05 -->|"source evidence"| S07

S05 -->|"source evidence"| S08


S09 -->|"ready project context"| S10


S06 -->|"architecture findings"| S10

S07 -->|"dependency findings"| S10

S08 -->|"design findings"| S10


S10 -->|"synthesized project context"| S11



%% =========================================================
%% Phase 2 — Main Implementation
%% =========================================================

S12["S12<br/>implement"]

S13["S13<br/>dispatching-parallel-agents"]

S14["S14<br/>subagent-driven-development"]

S15["S15<br/>parallel-feature-development"]

S16["S16<br/>ci-cd-and-automation"]


S11 -->|"implementation plan"| S12


S12 -->|"parallelizable work"| S13

S13 -->|"subagent tasks and status"| S14

S12 -->|"implementation progress"| S14


S14 -.->|"integrated changes require updates<br/>loop"| S12


S14 -->|"frontend implementation work"| S15

S14 -->|"backend implementation and integration"| S16

S15 -->|"integrated frontend changes"| S16



%% =========================================================
%% Phase 3 — Verification / Merge / Release
%% =========================================================

S17["S17<br/>github-pr-workflow<br/><br/>merge pull request"]

S19["S19<br/>release-management"]


S16 -.->|"checks failed<br/>on_failure"| S12

S16 -->|"all required checks passed"| S17


S17 -->|"release deployment required"| S19

S17 -->|"no release required"| S22

S19 -->|"release completed"| S22



%% =========================================================
%% Phase 4 — Independent Audit / Knowledge Maintenance
%% =========================================================

S18["S18<br/>architecture-audit"]

S20["S20<br/>agents-md"]

S21["S21<br/>documentation-maintenance"]


S18 -->|"update agent operating knowledge"| S20

S18 -->|"organize project documentation"| S21

S21 -->|"documentation synchronized"| S22



%% =========================================================
%% Phase 5 — Closeout
%% =========================================================

S22["S22<br/>engineering-closeout"]



%% =========================================================
%% Styling
%% =========================================================

classDef skill fill:#1f2222,stroke:#8b8f92,color:#eeeeee,stroke-width:1px;

classDef decision fill:#1f2222,stroke:#d4a72c,color:#eeeeee,stroke-width:2px;


class S01,S03,S04,S05,S06,S07,S08,S09,S10,S11,S12,S13,S14,S15,S16,S17,S18,S19,S20,S21,S22 skill;

class S02 decision;
```

(Dashed edges = dynamic edges: `loop` feedback edges and `on_failure` failure-return edges — the cycle check permits only these two kinds; any other cycle = validation failure.)

## 3. Phase-by-Phase Reading

| Layer | Nodes | Design Intent |
|---|---|---|
| **1. INTAKE** | S01→S02 | Entry is unclassified (request / idea / existing project all enter); **S02 is the cost controller** — routes by "what does this work need", so trivial tasks never traverse the full graph |
| **2. UNDERSTAND** | S03/S04/S09 | Requirements clarification (structured output) / bug fixing (returns to S01 for re-evaluation when done) / ready-context bypass |
| **3. CONTEXT** | S05→S10 | **Evidence first** (S05 extracts citable facts from the codebase) → three orthogonal views (S06 current state / S07 constraints / S08 target) → **S10 convergence hub**: all local facts synthesized into a single project state (PROJECT-CONTEXT.md) |
| **4. PLAN** | S11 | Understanding → executable plan, explicitly marking **parallelizable tasks** (triggers the subagent layer) |
| **5. EXECUTE** | S12→S15 | Main implementation → parallel detection (S13) → orchestration (S14, with an **integration feedback loop** back to S12) → parallel-stream integration (S15) |
| **6. VERIFY** | S16 | **Hard gate**: CI is the external verifier — "self-reported completion is a hypothesis, the gate is the test"; failure flows back along `on_failure` to S12 (execution-grounded recovery) |
| **7. CLOSEOUT** | S17→S22 | After merge, dual exit (no release → straight to closeout / release needed → S19) → S22 closeout archive; **S18 independent audit axis** (zero in-degree, runs in parallel) maintains machine knowledge (AGENTS.md) and human documentation, also converging into closeout |

## 4. How to Run

```
# 1. Validate (gate: must pass before running)
python workflow-definition/scripts/validate-workflow.py workflow.yaml
#    add --skills-dir PATH to also verify every node's skill resolves to an installed skill

# 2. Execute (per the workflow-runner protocol)
#    validate -> topological scheduling -> per-node (load the skill and execute) -> artifact passing
#    -> gates/branches/loops -> .workflow/state.json persistence (checkpoint recovery)
#    -> bounded retry on failure -> S22 produces the closeout report
```

## 5. Engineering Quality (Four Properties)

1. **Explicit structure**: 33 edges are defined before execution; scheduling does not depend on the agent's free will
2. **Structure/content separation**: the graph file vs the 22 skills — neither invades the other
3. **Executable semantics**: the runner's scheduling protocol (topology / gates / branches / loops / state / recovery)
4. **First-class engineering artifact**: version-controlled; the validator is CI-runnable (positive and negative cases both tested); state.json is monitorable
