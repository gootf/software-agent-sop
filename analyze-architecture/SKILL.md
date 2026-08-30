---
name: analyze-architecture
description: Deeply analyze codebase architecture and dependencies. Use when understanding system design, finding patterns, or mapping how components interact.
argument-hint: [component-or-feature]
context: fork
agent: Explore
allowed-tools:
  - Glob
  - Grep
  - Read
  - Bash(git *)
---

# Analyze Codebase Architecture

Perform deep architectural analysis of the target component or feature (per the user's request) without cluttering the main context.

## Analysis Goals

Investigate and document:

1. **Component Structure**
   - How is the target organized?
   - What are the main modules/files?
   - What patterns are being used?

2. **Dependencies & Relationships**
   - What does the target depend on?
   - What depends on the target?
   - Are there circular dependencies?
   - Are dependencies appropriately layered?

3. **Data Flow**
   - How does data flow through the target?
   - What are the inputs and outputs?
   - Where is state managed?
   - Are there side effects?

4. **Design Patterns**
   - What architectural patterns are used?
   - Are patterns applied consistently?
   - Are there anti-patterns present?

5. **Potential Issues**
   - Tight coupling between components?
   - Missing abstractions or too many abstractions?
   - Code duplication?
   - Complexity hotspots?

## Investigation Steps

### Step 1: Map the Territory

Use Glob to find all files related to the target:
```bash
# Find main component files
# Find tests
# Find documentation
# Find configuration
```

### Step 2: Understand Key Files

Read the most important files:
- Entry points
- Core business logic
- Public APIs
- Type definitions

For each file, note:
- Purpose and responsibilities
- Key functions/classes
- Exports and imports

### Step 3: Trace Dependencies

Use Grep to find:
- Import statements for the target
- References to key functions
- Test coverage

Create a dependency graph showing relationships.

### Step 4: Analyze Patterns

Look for:
- Consistent patterns (good)
- Pattern violations (investigate why)
- Missing patterns (opportunities)
- Overused patterns (complexity)

### Step 5: Generate Report

## Output Format

Provide a comprehensive report:

### Overview
- What is the target?
- What problem does it solve?
- Where does it fit in the larger system?

### Architecture Diagram
```
[ASCII diagram showing component structure]

Component A
├── Sub-component B
├── Sub-component C
└── Sub-component D
    ├── Module E
    └── Module F
```

### Key Components

For each major component:
- **Purpose**: What it does
- **Location**: File paths
- **Dependencies**: What it uses
- **Dependents**: What uses it
- **Complexity**: Lines of code, cyclomatic complexity if notable

### Data Flow

```
Input → [Component A] → [Component B] → Output
          ↓
      [Side Effect]
```

### Patterns Observed

- **Pattern 1**: Where it's used and why
- **Pattern 2**: Implementation details

### Issues & Recommendations

#### Issues
1. **Issue description**
   - Impact: High/Medium/Low
   - Location: file.ts:123
   - Recommendation: Specific action

#### Opportunities
1. **Improvement description**
   - Benefit: What would improve
   - Approach: How to implement

### Metrics

- Total files: X
- Total lines: Y
- Test coverage: Z%
- Key dependencies: List

## Notes

- This skill runs in a forked context to avoid cluttering your main conversation
- It can read many files without impacting your working context
- Results are summarized and returned to you when analysis completes
- Use when you need deep investigation without disrupting current work
