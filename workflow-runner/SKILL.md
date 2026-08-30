---
name: workflow-runner
description: "Execute a workflow.yaml graph — the scheduler protocol: validate the graph, topologically order nodes, execute each node via its skill, carry artifacts, apply gates/branches/loops/skips, persist state to .workflow/state.json, resume from checkpoints, and close with engineering-closeout. Use when a workflow.yaml exists and the user says run/continue/resume the workflow, execute the graph, or start the SOP."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [workflow, graph, execution, scheduler, sop]
    related_skills: [workflow-definition, engineering-closeout, delegation-protocol, synthesize-project-context]
---

# Workflow Runner (Graph Execution Protocol)

> Companion to `workflow-definition` (the graph file + validator). This skill is the **scheduler**: it consumes the declarative graph and executes it node by node. The graph owns sequencing; skills own content; this protocol owns execution.

## Inputs

- `workflow.yaml` at the project root (or explicit path).
- Optional: a starting node id (partial run) — otherwise run from the entry set.
- Optional: an argument/parameter to inject as the intake input.

## Execution Protocol

### Step 0 — Validate

Run the validator from the `workflow-definition` skill (from the repository root):

```
python workflow-definition/scripts/validate-workflow.py workflow.yaml
```

**Gate**: invalid graph → STOP. A workflow that fails validation must not run.

### Step 1 — Load state

- Read `.workflow/state.json` if present. Format:
  ```json
  {
    "workflow": "<name>", "version": "<semver>", "started": "<iso>",
    "nodes": { "<id>": { "status": "pending|running|passed|skipped|failed|blocked",
                          "at": "<iso>", "artifacts": ["<paths>"], "note": "<text>" } },
    "current": ["<ids ready to run>"]
  }
  ```
- No state file → initialize: all nodes `pending`, entry set = nodes with no incoming non-loop edges (plus `independent: true` nodes).
- State file exists → **resume**: continue from `pending`/`running` nodes. A `running` node found in state is treated as failed-attempt-1 (rerun once).

### Step 2 — Schedule (topological order)

- Compute the order from non-loop edges (Kahn's algorithm). `independent: true` nodes have no prerequisites — they can run at any time (audit axis).
- **Parallelism**: any set of ready nodes whose file sets do not overlap may run concurrently via background sub-agents (the parallel-execution mechanism of your harness). Serialize when file sets overlap (measured rule — see `subagent-driven-development`).

### Step 3 — Execute each node

For each ready node, in order:

1. **Precondition check** — all non-loop in-edges come from `passed` nodes; `skip_when` predicate evaluated (if true → mark `skipped`, follow the edge labeled for the skip path if declared, else continue downstream as if passed).
2. **Load the node's skill** — load the skill by name (e.g. `skill_view(<skill>)` in Hermes); the skill's workflow IS the node's execution.
3. **Execute** — run the skill's procedure with the node's `inputs` artifacts available; produce `outputs` artifacts (create parent dirs; paths relative to project root).
4. **Record** — update `state.json` immediately after the node: status, artifacts, note, timestamp. State is the only memory the scheduler trusts.
5. **Route** — after a node passes:
   - Gate node (has `on_pass`/`on_failure` edges): evaluate the gate condition (e.g. CI result) → follow the matching edge. Failure → the `on_failure` target becomes ready; the failure is recorded with its evidence.
   - Router node (≥2 outgoing edges): evaluate the edge labels (conditions) → exactly one edge is taken; record which in the node's note.
   - Chain node: follow its single outgoing edge.
   - Loop edges (`loop: true`) are taken only when the loop condition in the label fires (e.g. integration feedback, re-evaluation) — the target node is re-run (its status resets to `pending`; bound the retry to the label's stated limit or 2 attempts).

### Step 4 — Failure handling

- Node fails: mark `failed`, record evidence. If the node is a gate target with a declared recovery path (its in-edge label states recovery), follow it. Otherwise retry ONCE (same node, note "retry-1"); still failing → mark `blocked` and STOP with a report. Never loop silently.

### Step 5 — Completion

- When `final` node passes → run `engineering-closeout` (the closeout report is the workflow's terminal artifact).
- Verify: every node is `passed` or `skipped` (skips must be explainable by `skip_when` or a branch condition); state file shows `final: passed`.

## Conventions

- **Artifacts**: node `outputs` land under `artifacts/` by default (e.g. `artifacts/00-requirements.md`) unless the graph says otherwise. The runner never fabricates an artifact for a failed node.
- **Synthesis hubs** (nodes consuming many ancestors' outputs): gather all inputs BEFORE starting — `synthesize-project-context` is the reference procedure for the S10-style slot.
- **Independent axis**: audit-style nodes (`independent: true`, e.g. S18) run as a background track; their outputs feed the graph at the declared merge point (e.g. S21 → final).
- **Human checkpoints**: a node whose skill requires user decisions (a clarify-style prompt, batch confirm) pauses the runner — state.json marks it `running` with a note; resume after the user responds.
- **State is committable**: `.workflow/state.json` may be committed for auditability; it is the graph's monitoring output (readable by humans and CI).

## Anti-Patterns

- **Free-form execution** — the agent must follow the graph, not its own judgment about what to do next; if the graph is wrong, edit the graph, not the run.
- **Skipping validation** — an invalid graph produces an unpredictable run.
- **Writing state into workflow.yaml** — state belongs in state.json.
- **Unbounded loops** — every `loop: true` traversal needs a bound (label limit or 2-attempt default).
- **Ignoring branch labels** — the condition text on the taken edge is recorded; an untaken edge's label explains why (audit trail).
- **Parallel with overlapping files** — serialize overlapping file sets (measured: 3 parallel implementers with disjoint sets ran conflict-free; overlap → conflicts).
- **Fabricating artifacts** — a failed node's outputs do not exist; downstream must block, not imagine them.
