---
name: plan-and-review
description: >-
  Runs a native Cursor Plan-mode session, then grills remaining gaps and
  iterates an isolated review-pr loop on the plan until it converges. Use when
  the user is in Plan mode, asks for a planning session, asks to plan a
  non-trivial change, or names plan-and-review. Skip the grill and review loop
  if the user asks for a quick plan, no review, or to skip the review loop.
---
# Plan and Review

If you are following this skill, say so in your first output.

This skill **wraps** Cursor Plan mode. It does not replace it. Do not write a
custom planner, second intake interview, or parallel “planning process.”

## Escape hatch

If the user asks for a **quick plan**, **no review**, or to **skip the review
loop**: stay in native Plan mode only. Do not grill after the draft. Do not
launch reviews. Do not leave Plan mode just to satisfy this skill.

## Workflow

Track this checklist:

```
- [ ] 1. Native Plan mode (switch if needed)
- [ ] 2. First plan draft exists
- [ ] 3. Grill remaining gaps; shared understanding
- [ ] 4. Switch to Agent mode
- [ ] 5. Isolated review-fix loop (max 3 rounds)
- [ ] 6. Convergence judgment; wait (do not implement)
```

### 1. Enter native Plan mode

- If already in Plan mode, skip this step.
- Otherwise call `SwitchMode` with `target_mode_id: "plan"`. Wait for approval.
- After the switch, **let Plan mode’s built-in instructions drive** exploration,
  trade-offs, and the plan artifact. This skill only adds steps 3–6 around that.

### 2. First draft

Produce a complete first draft using native Plan mode. Identify the plan
artifact Cursor wrote (usually under `~/.cursor/plans/`). That file is the
object of grilling, review, and edits. If there is no file, write the in-chat
plan to a file so a subagent can read it.

**Do not grill yet.**

### 3. Grill gaps only

Read and follow the grilling skill (typically
`~/.agents/skills/grilling/SKILL.md`).

- Grill **only after** the first draft exists.
- Grill **only** decisions the draft left open, assumed, or skipped.
- Do not re-open topics the draft already settled unless a later review finding
  reopens them.
- One question at a time, with your recommended answer, per the grilling skill.
- Fold answers into the plan as you go.

Do not start the review loop until grilling has a **shared understanding**, or
there were no remaining decisions.

### 4. Leave Plan mode

Plan mode is read-only. The review-fix loop must edit the plan.

Call `SwitchMode` with `target_mode_id: "agent"`. Wait for approval. Then
continue in this same conversation.

### 5. Isolated review-fix loop

Max **3** rounds. Each round:

1. Launch a **fresh** `Task` subagent (`subagent_type: "generalPurpose"`,
   `run_in_background: false`). It must **not** receive this conversation’s
   history, prior reviews, triage, or your reasoning.
2. When it returns, **triage every finding** (accept / reject / defer) and
   **patch accepted items into the plan immediately**. Do not wait for the
   user per finding or per round. Print a triage table in this chat so they can
   interrupt.
3. If a stop condition hits, go to step 6. Otherwise launch the next round.

#### Subagent prompt (required contents)

Tell the subagent to **read and follow** the `review-pr` skill
(`skills/review-pr/SKILL.md` in the current repo if present, else
`~/.cursor/skills/review-pr/SKILL.md`).

Adapter (put this in the Task prompt, verbatim in substance):

- The subject is the **plan artifact**, not a git PR/branch.
- Follow `review-pr` for severity (`CRITICAL` / `WARNING` / `SUGGESTION`),
  focus areas, challenging false positives, completeness, and minimal change.
- Report findings against **plan sections/headings**, not git line diffs.
- Skip GitHub deep-links, compare-to-main, approval-to-merge, and “never
  open a PR” posting rules. Still emit the severity summary table.
- Mention that `review-pr` was used.

Give the subagent **only**:

1. Path to the current plan file (tell it to `Read` the file).
2. The original user request.
3. Grill decisions already settled.

Do **not** give: prior review output, your triage, rejected-finding lists, or
chat history.

#### Main-agent validity bar

- **Accept** if it changes scope, steps, risks, sequencing, missing work, or
  contradictions.
- **Reject** if false, duplicate, already addressed, or an implementation nit
  that does not belong in a plan.
- **Defer** only if it is real but belongs after implementation starts.

One-line reason per finding. Suggestions-only: do not auto-apply leftover
`SUGGESTION`s unless they are required for the plan to be coherent.

### 6. Stop, judge convergence, wait

Stop on the **first** of:

1. Latest isolated review has **no CRITICAL and no WARNING**.
2. The round produced **zero accepted** findings (all rejected, deferred, or
   duplicates).
3. **Three** review rounds have completed.

Then, in this chat:

- State whether the loop **actually converged** (not just that a stop rule
  fired).
- Recommend whether **more review rounds** are worth it. If the cap was hit
  with leftover CRITICAL/WARNING, say so explicitly — do not pretend it
  converged.
- **Do not implement.** Wait for the user.

The user may interrupt at any time; treat that as a stop.
