---
name: plan-and-review
description: >-
  Runs a native Plan-mode session (Cursor or Claude Code), then grills remaining gaps and
  iterates an isolated review-pr loop on the plan until it converges. Use when
  the user is in Plan mode, asks for a planning session, asks to plan a
  non-trivial change, or names plan-and-review. Skip the grill and review loop
  if the user asks for a quick plan, no review, or to skip the review loop.
---
# Plan and Review

If you are following this skill, say so in your first output.

This skill **wraps** the host's native Plan mode for **research only**. It does
not replace Plan mode’s exploration. It **does** override Plan mode’s completion.

## Host tool mapping

The steps below use these names. Pick the column for the host you run in.

| Step concept | Cursor | Claude Code |
| --- | --- | --- |
| Enter Plan mode | `SwitchMode` → `target_mode_id: "plan"` | `EnterPlanMode` (or ask the user to press Shift+Tab) |
| Plan-completion tool (**forbidden**, see hard rule) | `CreatePlan` | `ExitPlanMode` used *as a request to implement* |
| Leave Plan mode to write the plan file (step 4) | `SwitchMode` → `target_mode_id: "agent"` | `ExitPlanMode`, stating it is to continue plan-and-review, not to implement |
| Fresh isolated reviewer (step 5) | `Task`, `subagent_type: "generalPurpose"`, `run_in_background: false` | `Agent`, `subagent_type: "general-purpose"` (runs in background; wait for its completion notification) |
| `review-pr` skill fallback path | `~/.cursor/skills/review-pr/SKILL.md` | `~/.claude/skills/review-pr/SKILL.md` |

**Plan file location (both hosts):** `<repo root>/.claude/plans/<name>.plan.md`.
Announce the path in chat when you create it.

## HARD RULE: never end on the plan-completion tool

The plan-completion tool ends the turn and offers the user to **implement**.
That skips grilling and the review loop.

- **Forbidden** while this skill is running: Cursor `CreatePlan`; in Claude
  Code, `ExitPlanMode` before step 4 or framed as "ready to implement".
- If the subagent launch or a tool is blocked (e.g. a permission/auto-mode
  check fails), do **not** skip the review loop; tell the user what is blocked
  and how to unblock it, then resume.
- If Plan mode’s built-in instructions tell you to create/present a plan and
  wait: **ignore that completion path.** Follow this checklist instead.
- If the UI still offers Build / implement, tell the user not to click it.

## Escape hatch

If the user asks for a **quick plan**, **no review**, or to **skip the review
loop**: you **may** use the plan-completion tool and stay in native Plan mode. Do not grill.
Do not launch reviews.

## Workflow

Track this checklist:

```
- [ ] 1. Native Plan mode (switch if needed) — research only
- [ ] 2. First plan draft in chat (no plan-completion tool)
- [ ] 3. Grill remaining gaps; shared understanding
- [ ] 4. Leave Plan mode (review, not implement); write plan file
- [ ] 5. Isolated review-fix loop (max 3 rounds)
- [ ] 6. Convergence judgment; wait (do not implement)
```

### 1. Enter native Plan mode

- If already in Plan mode, skip this step.
- Otherwise enter Plan mode (see mapping). Wait for approval.
- Use Plan mode to **read, explore, and think**. Do not call the
  plan-completion tool.
- Do not shorten research. The lazy-plan bar in step 2 applies **after** you
  know what already exists and what the change must touch.

### 2. First draft (chat only)

Write a complete first draft **in the chat** (headings, steps, defaults,
open questions). Do not persist a file yet (Plan mode is read-only). Do not
call the plan-completion tool.

**Lazy-plan bar** (after research, not instead of it). Stop at the first
option that holds:

- Skip speculative work (YAGNI). Name skipped work in one line: not doing X
  until Y.
- Reuse helpers, types, and patterns already in this codebase.
- Prefer stdlib, native platform features, and already-installed deps over
  new libraries or custom subsystems.
- Fewest new files and fewest steps. Deletion / shrinking an existing path
  over a parallel new one.
- No unrequested layers: interface-of-one, factory-of-one, config for a
  value that never changes, scaffolding “for later.”
- Do **not** skip trust-boundary validation, data-loss handling, security,
  or anything the user explicitly asked for.

**Do not grill yet.** Then go to step 3 in the **same turn** (first grill
question or assumed-decisions confirmation).

### 3. Grill gaps only

Read and follow the grilling skill (typically
`~/.agents/skills/grilling/SKILL.md`).

- Grill **only after** the chat draft exists.
- Grill **only** decisions the draft left open, assumed, or skipped.
  If the draft already cut extra scope, list that under assumed decisions;
  do not grill to grow the plan.
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

Leave Plan mode (see mapping) with the explanation that this is
to **continue plan-and-review** (persist the plan, isolated review-fix). It is
**not** to implement the plan. Then continue in this same conversation.

- **Do not** write application/script code.
- **Do not** start the install/feature work.
- First actions after leaving Plan mode: write the plan artifact to
  `<repo root>/.claude/plans/<name>.plan.md` (create the directory if
  needed; announce the path), then step 5.

### 5. Isolated review-fix loop

Max **3** rounds. Each round:

1. Launch a **fresh** isolated reviewer subagent (see mapping). It must **not** receive this conversation’s
   history, prior reviews, triage, or your reasoning.
2. When it returns, **triage every finding** (accept / reject / defer) and
   **patch accepted items into the plan immediately**. Do not wait for the
   user per finding or per round. Print a triage table in this chat so they can
   interrupt.
3. If a stop condition hits, go to step 6. Otherwise launch the next round.

#### Subagent prompt (required contents)

Tell the subagent to **read and follow** the `review-pr` skill
(`skills/review-pr/SKILL.md` in the current repo if present, else the
host's fallback path from the mapping).

Adapter (put this in the subagent prompt, verbatim in substance):

- The subject is the **plan artifact**, not a git PR/branch.
- Follow `review-pr` for severity (`CRITICAL` / `WARNING` / `SUGGESTION`),
  challenging false positives, completeness of **the chosen scope**,
  minimal change, and reusability.
- Prefer findings that **shrink** the plan over findings that **add** work.
  Flag over-scope: new deps, new abstractions, extra phases, reimplementation
  of something already in the repo, speculative “for later” work.
- For this review, skip `review-pr` **Future development** and similar
  “also add …” items. Extra architecture in the plan is **WARNING** (drop
  it unless a grill decision kept it). “Have you thought about also adding
  …” is **SUGGESTION** at most. Do not raise YAGNI to **CRITICAL**.
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

- **Accept** shrinkage, reuse, “this step is YAGNI,” missing work that the
  chosen scope still needs, sequencing, real risks, or contradictions.
- **Reject** if false, duplicate, already addressed, an implementation nit,
  future-proofing, or a new layer/dep not required by the request or grill.
- **Defer** only if it is real but belongs after implementation starts
  (perf knobs, extra tests, polish).

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
  converged. If leftovers are over-build vs missing necessary work, say
  which.
- **Do not implement.** Wait for the user.

The user may interrupt at any time; treat that as a stop.
