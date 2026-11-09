---
name: regression-hunt
description: Find why something that worked before now fails (regression, "broke", "no longer works", "stopped working", "started failing after a change", "since commit X", git bisect). Use before building any fix for it. Not for bugs that never worked.
---

# Regression hunt

Work in a throwaway worktree or copy of the repository, never in the main checkout; keep patches, logs and traces in the project's scratch location, not in a tracked directory.

1. Name a known-good and a known-bad version. Read the diff between them and write down a hypothesis.
2. Cheapest discriminating trace next: run both versions up to the same point and log the first step, output or state that differs. A throwaway patch of about 20 lines, never committed.
3. If the hypothesis and the trace do not name the cause, eliminate: bisect the versions, or switch suspected pieces off one at a time and then together, with a time cap long enough for the good version to finish. Record every result in the plan or scratch file.
4. Build a fix variant only for a cause the trace names. If none is named, stop and report; do not try variants to find out.
5. A variant must pass the project's existing safety tests before any long run; a variant that breaks them is dropped and its patch saved in the scratch location. Confirm that the failing path is the one production uses before tuning anything to make a test pass.
