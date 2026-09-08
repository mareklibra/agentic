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

This skill **wraps** Cursor Plan mode for **research only**. It does not
replace Plan mode’s exploration. It **does** override Plan mode’s completion.

## HARD RULE: never call `CreatePlan`

`CreatePlan` ends the turn. Cursor then asks the user to switch to Agent to
**implement**. That skips grilling and the review loop.

- **Forbidden** while this skill is running: `CreatePlan`.
- If Plan mode’s built-in instructions tell you to create/present a plan and
  wait: **ignore that completion path.** Follow this checklist instead.
- If the UI still offers Build / implement, tell the user not to click it.

## Escape hatch

If the user asks for a **quick plan**, **no review**, or to **skip the review
loop**: you **may** use `CreatePlan` and stay in native Plan mode. Do not grill.
Do not launch reviews.

## Workflow

Track this checklist:

```
- [ ] 1. Native Plan mode (switch if needed) — research only
- [ ] 2. First plan draft in chat (no CreatePlan)
- [ ] 3. Grill remaining gaps; shared understanding
- [ ] 4. Switch to Agent (review, not implement); write plan file
- [ ] 5. Isolated review-fix loop (max 3 rounds)
- [ ] 6. Convergence judgment; wait (do not implement)
```

### 1. Enter native Plan mode

- If already in Plan mode, skip this step.
- Otherwise call `SwitchMode` with `target_mode_id: "plan"`. Wait for approval.
- Use Plan mode to **read, explore, and think**. Do not call `CreatePlan`.

### 2. First draft (chat only)

Write a complete first draft **in the chat** (headings, steps, defaults,
open questions). Do not persist a file yet (Plan mode is read-only). Do not
call `CreatePlan`.

**Do not grill yet.** Then go to step 3 in the **same turn** (first grill
question or assumed-decisions confirmation).

### 3. Grill gaps only

Read and follow the grilling skill (typically
`~/.agents/skills/grilling/SKILL.md`).

- Grill **only after** the chat draft exists.
- Grill **only** decisions the draft left open, assumed, or skipped.
- Do not re-open topics the draft already settled unless a later review finding
  reopens them.
- One question at a time, with your recommended answer, per the grilling skill.
- Fold answers into the in-chat draft as you go.

If you believe nothing is open: **do not skip silently.** List the assumed
decisions and wait for the user to confirm. That confirmation **is** the
shared understanding.

Do not start the review loop until that shared understanding exists.

### 4. Leave Plan mode (not to implement)

Plan mode is read-only. The review-fix loop must write a plan file.

Call `SwitchMode` with `target_mode_id: "agent"` and explanation that this is
to **continue plan-and-review** (persist the plan, isolated review-fix). It is
**not** to implement the plan. Then continue in this same conversation.

- **Do not** write application/script code.
- **Do not** start the install/feature work.
- First Agent-mode actions: write the plan artifact (usually
  `~/.cursor/plans/<name>.plan.md` or a path you announce), then step 5.

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
