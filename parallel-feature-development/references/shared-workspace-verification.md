# Worked Example: Verifying Popup Changes While T1/T2 Agents Were Mid-Edit

Context: Chrome-extension repo, 22-slot parallel workflow (T1 = contract/types+background, T2 = options page, T3 = popup). All agents on ONE working tree. T3's brief forbade touching `src/background.ts`, `src/content/content.ts`, `src/options/`, contract files.

## The Failure Pattern

First `npx tsc --noEmit` run → 6 errors, ALL in files I didn't own:

```
src/background.ts(3,79):  error TS6196: 'ImageFormat' is declared but never used.
src/background.ts(77,60): error TS2554: Expected 2 arguments, but got 3.
src/background.ts(79,58): error TS2554: Expected 2 arguments, but got 3.
src/background.ts(81,56): error TS2554: Expected 2 arguments, but got 3.
src/background.ts(93,12): error TS2304: Cannot find name 'isJpeg'.
src/options/options.ts(3,62): error TS6196: 'ImageFormat' is declared but never used.
```

Tempting failure mode: "the build is red, fix it." WRONG — all six are in other agents' files.

## Attribution (proof I wasn't the cause)

1. `git status --short` → `src/background.ts`, `src/options/*`, `src/types/index.ts`, `src/utils/settings.ts` already `M` (modified) in working tree before my session. My only writes: `src/popup/index.html`, `src/popup/popup.ts`.
2. My files appeared in ZERO of the reported errors → my changes compile cleanly in the shared project.
3. Errors were self-inconsistent (line 131 had a 3-param signature while the compiler claimed 2) → the file's on-disk state was changing under the compiler.

## Drift Detection (the decisive evidence)

Re-ran tsc ~30s later → different error set:

```
run 2: src/content/content.ts(38,35): error TS2554: Expected 0 arguments, but got 1.
run 3: src/content/content.ts(277,38): error TS6133: 'options' is declared but its value is never read.
```

Error files AND lines moved between runs → another agent actively editing. Pattern: `for i in 1..6; do sleep 15; npx tsc --noEmit && break; done` → run 1 after the loop started came back CLEAN (exit 0).

## Final Gate

Re-ran all three verifications fresh in one chain after the sibling settled:

```bash
cd "path/to/project" && npx tsc --noEmit && echo TSC_OK \
  && npx vitest run 2>&1 | tail -6 \
  && npm run build 2>&1 | tail -8; echo "FINAL_EXIT=$?"
```

- `tsc --noEmit` → TSC_OK (0 errors)
- `vitest run` → 13 passed
- `npm run build` → exit 0
- Reported the converging clean run as evidence; documented the transient noise in the report's concerns section, including "I did not touch contract files."

## Tooling Quirks on This Windows Host (workarounds, not blockers)

- `search_files` with `path: "D:/..."` failed with `rg: /d/Project/...: IO error ... cannot find the path specified` — it MSYS-translates the path and can miss drives other than C:. `read_file` with native `D:/...` works fine.
- The `patch` tool's post-edit lint can false-positive the same way (`error TS6053: File '/d/Project/MyProject/...' not found`) even though the patch applied. Ignore the lint noise; real verification is `npx tsc --noEmit` run from inside the repo dir.
- Reliable content search on other drives: `cd "F:/repo" && grep -n pattern src/...` via terminal.

## Why This Matters

In a single-tree parallel workflow, transient red runs are the NORM, not the exception. The discipline is: attribute → drift-check → wait for convergence → report clean evidence + document the noise. Never "fix" other owners' files to make your gate green — the brief's ownership rules outrank the build.
