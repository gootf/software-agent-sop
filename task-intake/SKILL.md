---
name: task-intake
description: "Use at the beginning of a new task. Ensures you fully understand the requirements, boundaries, and acceptance criteria before writing code."
---

# Task Intake Protocol

Never start implementing blindly. When you receive a new task, you must force clarification of boundaries and expected outcomes.

## Intake Checklist

1. **What is the goal?** Summarize the user's request in your own words.
2. **What is out of scope?** Identify what you are *not* going to do. If the user asked to fix a button, do not refactor the routing layer.
3. **How will we test it?** Define the validation criteria. Will it be a unit test, a manual UI check, or a curl command?
4. **What context is missing?** Ask the user for specific files, logs, or environment details if the request is too vague.

## Anti-Pattern: The Blind Start
Do not say "I will now fix the bug." and immediately edit files. Instead, use a repo-map or grep to confirm the files exist, then state your understanding of the problem. If the user's instruction is ambiguous, explicitly pause and ask them a clarifying question.

## Anti-Pattern: Defaulting to the Old Tech Stack on Rebuild/Redo

When the user says "redo this project" (refactor/rewrite), **the old project's tech stack is not a requirement**. Technology selection must happen AFTER requirements are confirmed — choosing the stack first is deciding for the user. Real correction case: rebuilding an existing project, the assistant wrote the README and .gitignore for the old stack without confirming requirements; the user corrected: "We don't necessarily need the old stack. Choose based on requirements. You haven't even confirmed my requirements."

Correct order (the user expects you to run a SOP, not guess):

1. `interview-me`: one question at a time — confirm scope / target platform / constraints / success criteria / out-of-scope, until confidence ≥95% with an explicit yes
2. `spec-driven-development`: write a spec (tech-stack choice goes in the spec with rejected alternatives and reasons)
3. Only after requirements are clear, choose the stack; when the stack is free, give **one** best recommendation + a rejected-alternatives comparison — don't list a menu of options

Trigger: the user says "stack is up to you / you pick / find the best" = authorization to decide the stack, but requirements still come first.