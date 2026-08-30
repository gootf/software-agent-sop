---
name: workflow-definition
description: "Define an agent workflow graph as a first-class engineering artifact — workflow.yaml schema (mermaid-flowchart-flavored: node blocks + explicit edge list), validation rules (pass/fail gates), and a zero-dependency validator script for CI. Use when creating or editing a workflow.yaml, when asked to define the workflow, write the graph as yaml, or when validating that a workflow definition is well-formed and its skills exist."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [workflow, graph, yaml, definition, sop]
    related_skills: [workflow-runner, agent-workflow-engineering, importing-external-skills]
---

# Workflow Definition (Graph as Engineering Artifact)

> Companion to `workflow-runner` (execution protocol) and `agent-workflow-engineering` (design principles). This skill owns the **declarative graph format** — the explicit structure that runs before the agent does. Control flow lives in `workflow.yaml`; skill content lives in the skills; the two never mix.
>
> **Format philosophy**: the YAML reads like the mermaid `flowchart TB` blocks — node blocks carry identity, a single `edges:` list carries ALL arrows (with `label:` as the arrow text), and routing semantics (branch condition / pass-fail / loop) are edge properties, not hidden fields.

## The Graph File

- One file per workflow: `workflow.yaml` at the project root (or `.workflow/workflow.yaml` for multi-workflow projects).
- **Committed to version control** — the graph is core code, not documentation.
- Execution state is NEVER written into this file (state lives in `.workflow/state.json`, owned by `workflow-runner`).

## Schema (v1.1)

```yaml
name: <workflow name>            # required
version: <semver>                # required
description: <one line>          # optional
nodes:                           # required, non-empty — node blocks (like mermaid S01["..."] / S02{...})
  - id: <unique node id>         # required, unique
    skill: <installed skill name># required — the node's executable unit
    role: <node role>            # required: intake | router | context-builder | executor | coordinator | validator | knowledge | closeout
    description: <one line>      # optional
    inputs: [<artifact path>]    # optional — consumed artifacts
    outputs: [<artifact path>]   # optional — produced artifacts
    independent: <true|false>    # optional, default false — zero in-degree start (audit axis)
edges:                           # required, non-empty — ALL arrows in one list (mermaid `A --> B` / `A -->|label| B`)
  - from: <node id>              # required
    to: <node id>                # required
    label: <edge text>           # optional — arrow label: branch condition / artifact name / pass-fail condition
    via: [<artifact path>]       # optional — artifacts carried by this edge
    kind: <normal|on_pass|on_failure>  # optional, default normal — gate edges
    loop: <true|false>           # optional, default false — feedback/back edge (S14→S12, S04→S01). The ONLY legal way to form a cycle.
final: <node id>                 # required — the unique terminal node
```

- **Routing semantics live on edges, not in nodes**: a router node is just a node with ≥2 outgoing edges (labels carry the conditions); a hard gate is a node with one `kind: on_pass` and one `kind: on_failure` edge; a feedback loop is an edge with `loop: true`.
- Artifacts are paths relative to the project root. A node's `inputs` may be produced by its direct predecessor, ANY ancestor (synthesis hubs), or a loop (integration feedback).

## Validation Gates (run before execution, and in CI)

`scripts/validate-workflow.py workflow.yaml [--skills-dir <path>]` — zero-dependency Python 3 (stdlib only), exit 0 = valid / exit 1 = invalid with reasons. Checks, in order:

1. **Parse** — the file parses as the supported YAML subset (maps/lists/scalars/comments; no anchors, no multi-line strings). Parse error = fail.
2. **Required fields** — `name`, `version`, `nodes` (non-empty), `edges` (non-empty), `final` present; `final` is a defined node id.
3. **Node identity** — ids unique; `skill` and `role` present; role ∈ {intake, router, context-builder, executor, coordinator, validator, knowledge, closeout}.
4. **Edge integrity** — every edge `from`/`to` references a defined node; `from != to`; `kind` ∈ {normal, on_pass, on_failure}; `loop` is boolean.
5. **Cycle check** — cycles are legal ONLY through `loop: true` edges (feedback/re-evaluation) and `kind: on_failure` edges (execution-grounded recovery: gate failure → implementation). Any other cycle = fail.
6. **Artifact closure (two levels)** — ERROR: an `inputs` artifact that NO node in the whole graph produces; WARNING: an input not produced by the node's ancestor closure (legitimate for branch/loop products — record, don't fail).
7. **Router completeness** — a node with ≥2 outgoing edges needs no extra declaration (labels are the conditions); a node with exactly 1 outgoing edge is a plain chain step.
8. **Gate completeness** — a node with a `kind: on_pass` edge MUST also have a `kind: on_failure` edge (and vice versa); each gate node has exactly one of each.
9. **Independent-axis rule** — `independent: true` nodes have NO incoming edges except `loop: true` ones (they start on their own).
10. **Terminal rule** — `final` has no outgoing edges except `loop: true` ones.
11. **Skill existence** — every `skill` resolves to an installed skill under `--skills-dir`. Default: `~/AppData/Local/hermes/skills` when present (Hermes installs); otherwise the check is skipped — pass `--skills-dir PATH` to enable it anywhere. Fail = skill missing.

## CI Integration

```yaml
# .github/workflows/workflow-check.yml (example)
# steps: checkout → python scripts/validate-workflow.py workflow.yaml --skills-dir . → fail on non-zero
```

- The validator is the graph's unit test: **a workflow that fails validation must not run**.
- Regression guard: `scripts/test-validate-workflow.py` runs the reference 22-slot workflow (must stay VALID) plus 3 negative cases (dangling edge/unknown skill, unmarked cycle, self-loop — must stay INVALID). Run it after ANY change to `validate-workflow.py`; exit 0 = all pass.
- Version bumps in `workflow.yaml` accompany graph-structure changes (same discipline as code).

## Anti-Patterns

- **Edges as prose** — arrows must be declarative `edges:` entries, not paragraphs in a README.
- **State in the graph file** — `.workflow/state.json` is the runner's; never commit execution state into workflow.yaml.
- **Hidden cycles** — every loop must be an explicit `loop: true` edge (integration feedback, re-evaluation); an unmarked cycle is a defect the validator must catch.
- **Duplicate declarations** — skill content does not restate the graph (structure/content separation): a skill must not hardcode "call S06 next"; the graph owns sequencing.
- **Overloaded nodes** — a node that is router AND gate AND loop target is probably several nodes; split it.
- **Label-less branching** — a router's outgoing edges without labels hide the conditions; every branch edge carries its decision text.
