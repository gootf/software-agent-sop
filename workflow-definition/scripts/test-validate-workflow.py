#!/usr/bin/env python3
"""Regression tests for validate-workflow.py (schema v1.1) — run after ANY validator change.

Usage:  python test-validate-workflow.py [path/to/validate-workflow.py] [path/to/workflow.yaml]
Exit:   0 = all pass, 1 = any fail. Prints PASS/FAIL per case.

Cases: 1 positive (the reference 22-slot workflow.yaml) + 3 negative
(dangling edge + unknown skill; unmarked cycle; self-loop). Mirrors the ad-hoc
verification run of 2026-08-11 (hermes-verify-workflow.py, Temp).
"""
import subprocess, sys, tempfile, os

HERE = os.path.dirname(os.path.abspath(__file__))
VALIDATOR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "validate-workflow.py")
# Default workflow = the skill-bundled template (decoupled from any external project dir);
# pass an explicit path to test another workflow.yaml.
WORKFLOW = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "templates", "workflow.example.yaml")

BAD = {
    "bad-dangling-and-skill": "name: b1\nversion: 0.0.1\nnodes:\n  - id: A\n    skill: nonexistent-skill-xyz\n    role: executor\n  - id: B\n    skill: task-intake\n    role: intake\nedges:\n  - from: A\n    to: Z\nfinal: B\n",
    "bad-unmarked-cycle": "name: b2\nversion: 0.0.1\nnodes:\n  - id: A\n    skill: task-intake\n    role: intake\n  - id: B\n    skill: task-intake\n    role: intake\nedges:\n  - from: A\n    to: B\n  - from: B\n    to: A\nfinal: B\n",
    "bad-selfloop": "name: b3\nversion: 0.0.1\nnodes:\n  - id: A\n    skill: task-intake\n    role: intake\nedges:\n  - from: A\n    to: A\nfinal: A\n",
}

def run(path, want_valid):
    r = subprocess.run([sys.executable, VALIDATOR, path], capture_output=True, text=True)
    ok = (r.returncode == 0) == want_valid
    print("%s %-36s rc=%d -> %s" % ("PASS" if ok else "FAIL", os.path.basename(path),
          r.returncode, "VALID" if r.returncode == 0 else "INVALID"))
    if not ok:
        print((r.stdout + r.stderr).strip()[:400])
    return ok

res = [run(WORKFLOW, True)]
with tempfile.TemporaryDirectory() as td:
    for n, c in BAD.items():
        p = os.path.join(td, n + ".yaml")
        with open(p, "w", encoding="utf-8") as f:
            f.write(c)
        res.append(run(p, False))
print("RESULT: %d/%d passed" % (sum(res), len(res)))
sys.exit(0 if all(res) else 1)
