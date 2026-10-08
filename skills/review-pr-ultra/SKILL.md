---
name: review-pr-ultra
description: Deep, cross-model-verified review of a PR/branch, source file, or plan/doc. Combines review-pr's checklist (unmodified) with review-council's multi-model verification when available, degrading honestly to a solo-model review when it isn't.
---

# Review PR Ultra

## What this does

Runs two independent full review passes against the same target and merges
them into one report:

- **Pass A** — the `review-pr` skill, completely unmodified. This guarantees
  review-pr-ultra finds everything `/review-pr` finds today — a strict
  superset, never a replacement.
- **Pass B** — the `review-council:run` plugin skill, when it's installed and
  a real second model family is available. Adds independent, cross-model
  corroboration on top of Pass A.

If review-council isn't available, or doesn't have enough reviewer families,
this degrades to a solo Pass-A run — honestly labeled as such, never silently
presented as verified.

Always state that this skill was used, and that it ran `review-pr` (Pass A)
and, if applicable, `review-council:run` (Pass B), in the final report.

## Step 1 — Target detection

Do not build a unified detection step. Forward the user's raw argument or
request unchanged to each pass; each skill uses its own existing detection.
review-council's auto-detect chain (open PR → staged → unstaged) doesn't
cover a fully committed local branch with no PR yet open — review-pr's own
headline case — so a shared detection step would regress exactly that case.
Pass A keeps review-pr's natural-language interpretation (including diffing
a committed branch against upstream main when there's no open PR); Pass B
keeps review-council's own auto-detect, unchanged.

**Known limitation.** For a fully committed local branch with no open PR and
a clean working tree, review-council's auto-detect cannot resolve a target
either, and has no "diff against upstream main" mode. Before invoking Pass B,
run this cheap precheck to catch that specific scenario:

```bash
gh pr view                                          # no open PR?
git diff --cached --quiet && git diff --quiet       # no staged/unstaged changes to tracked files?
```

(Use the tracked-file diff check, not a generic "clean `git status`" —
untracked files are irrelevant to review-council's own detection and a
`git status`-based check would miss cases it shouldn't.)

If both are true: skip Pass B for this run — don't let review-council prompt
the user mid-run — and go straight to Step 7 (degraded-mode report). Pass A's
coverage is unaffected; only cross-model verification is skipped for this run.

## Step 2 — Availability check (gate for Pass B)

Check whether `review-council:run` appears in the current skill listing. If
it does, invoke `review-council:setup` and read **only its per-provider
detection lines** (Codex / Google / Perplexity availability) — not its own
headline "council mode ready" verdict, which is satisfiable by Perplexity
alone and would disagree with the gate below. Decline or skip any unrelated
interactive prompts `review-council:setup` raises (yq install consent,
config-file scaffold offer) — those belong to a one-time setup flow, not
something to surface on every `/review-pr-ultra` run.

**Gate for running Pass B:** Claude plus at least one **repo-capable** second
family — Codex or Google (agy/gemini). Perplexity alone does not satisfy the
gate: it's diff-only/tool-less, and can't serve as a Step 6 double-check
verifier either (same rule review-council itself applies — never route
code-tracing findings to Perplexity).

If the plugin isn't installed, or the gate isn't met: skip Pass B entirely
and go to Step 7 (degraded-mode report) once Pass A completes.

## Step 3 — Pass A: `review-pr`, unmodified

Invoke the `review-pr` skill against the target exactly as it runs
standalone. It produces its full finding set (every existing focus area),
each with file, line, severity, title, and paste-ready comment.

For file/plan targets (not PR/branch), apply review-pr's checklist directly
to the file/plan content — skip the diff-against-upstream-main and
approval-recommendation parts of its instructions, since those only make
sense for a PR/branch target.

## Step 4 — Pass B: `review-council:run` (conditional)

Only if Step 2's gate passed. Invoke it against the same target,
**sequentially after Pass A, in the main conversation** — not backgrounded —
because review-council has its own interactive gates (e.g. a missing
configured static-analysis tool) that need a live user to answer.

review-council's own instructions are written to resist early termination
(reaching its Step 6.6 is framed as a stage that must always be offered, not
one that may be silently dropped). Override that explicitly: as part of
invoking `review-council:run`, tell it outright that this run ends at
*review-council's own* Step 6 (Report), and *review-council's own* Step
6.6 (digest posting) and Step 7 (learnings capture) must not be reached —
regardless of that plugin's own config. (Those step numbers belong to
review-council's internal numbering, distinct from this skill's own steps.)

Capture its judge ledger and report (findings, severity, badges).

**Skip Pass B** (go to Step 7) on any of three conditions:
1. Step 2's gate wasn't met, or the plugin isn't installed.
2. Step 1's precheck found no open PR and a clean tracked-file diff (the
   committed-branch known-limitation case).
3. Pass B was invoked but review-council's own run aborted mid-execution
   (e.g. every available provider failed at runtime). In this case, Pass A's
   already-complete results are still reported via Step 7 — never discarded.

## Step 5 — Merge

Union Pass A's and Pass B's findings by semantic fingerprint (file +
symbol/area + concern) — this is your own judgment call, the same kind of
semantic matching review-council's judge already does, not a script.

Severity scale mapping: review-pr CRITICAL = review-council critical;
review-pr WARNING = review-council important; review-pr SUGGESTION =
review-council suggestion.

Pass A's findings have no structured `symbol`/`concern` fields (review-pr
only emits a title + paste-ready comment) — infer them from that text. This
is a looser match than review-council's own same-schema dedup: when a match
is ambiguous, treat the two findings as separate rather than silently
merging unrelated ones.

- **Same finding in both** → keep once, severity = the more severe of the
  two ratings. Badge: keep review-council's native badge if it's already
  `[verified]` or `[cross-reviewed]` (already the strongest signal);
  otherwise (native badge was `[1 reviewer · unverified]`, `[unverified]`,
  or `[tool-only:<rule>]`) upgrade to `[cross-checked]` — two independent
  pipelines reaching the same finding is itself cross-pipeline
  corroboration, even if council's own internal reviewers didn't agree among
  themselves. (Edge case, not worth engineering around unless observed in
  practice: if Pass B silently degrades to a single reviewer mid-run — not a
  full abort — this upgrade slightly overstates independence.)
- **Council-only** → include, rendered in review-pr's output format (Step 8).
- **Review-pr-only** → pass to Step 6.

## Step 6 — Independent double-check (CRITICAL/WARNING review-pr-only findings only)

SUGGESTION-tier review-pr-only findings skip this step entirely — tag them
`[unverified]` directly in the final report.

**Choosing the verifier.** If more than one repo-capable second family is
available (both Codex and Google), prefer Codex; fall back to Google only if
Codex isn't available.

**Batch, don't call once per finding.** Batch every review-pr-only
CRITICAL/WARNING finding routed to that family into a **single** dispatch —
this avoids paying a slow cold start (e.g. `agy`'s multi-minute first call)
per finding, matching review-council's own batching pattern. Give each
finding a short `<finding-id>` in the dispatch and ask the verifier to echo
it back on each verdict line, in the exact shape:

```
<finding-id> | VERDICT — evidence
```

Because this is parsed by `rc-invoke-provider.sh`'s own output classifier
(below), `<finding-id>` must use only its required charset — alphanumerics
plus `._:-`, no spaces — and the verdict word must be exactly one of
`upheld` / `refuted` / `inconclusive`. A differently-shaped id or line risks
the script misclassifying a valid batch response as empty/failed output.

**Dispatch mechanism.** Reuse review-council's own `rc-invoke-provider.sh`
rather than re-deriving its safety behavior by hand — it already closes the
child's stdin and applies a hard TERM-then-KILL timeout, which a bare CLI
call does not (review-council's own history records a production bug where a
healthy Codex reviewer hung for the full timeout from exactly this gap):

```
rc-invoke-provider.sh <primary-bin> <fallback-bin> <prompt-file>
```

Locate the script under the installed review-council plugin's own directory
(resolve its install path the same way `review-council:setup`/`:run` would,
then join `scripts/rc-invoke-provider.sh`) — don't assume `CLAUDE_PLUGIN_ROOT`
is set outside review-council's own orchestration context. This is a soft
dependency on an unversioned internal file of a third-party plugin that
could change between review-council releases — accepted as a tradeoff since
it's strictly safer and less code than reimplementing stdin-closing +
hard-timeout behavior from scratch.

If the second family is Codex and it's MCP-only (no CLI binary present),
call `mcp__codex__codex` directly instead — this path has no script to
reuse, so it keeps its own stdin/timeout handling as a Task-tool dispatch.

**Harness timeout sizing.** Invoking the script is still a Bash-tool call,
and the harness's own Bash tool has a default 120000 ms timeout and a
600000 ms ceiling — shorter than the script's own default 600s internal cap,
let alone `agy`'s documented multi-minute cold start. Use the identical
sizing/escalation rule review-council's own "Reviewer: Codex"/"Reviewer:
Google" sections use for this same script call:

- Cap the foreground attempt at `FG_CAP = min(<reviewer_timeout_seconds>, 570)`
  seconds (default `reviewer_timeout_seconds` is 600, so `FG_CAP` defaults to
  570).
- Set `RC_REVIEWER_TIMEOUT=<FG_CAP>` as the env var for the script
  invocation.
- Set the Bash **tool's own** `timeout` parameter to `(FG_CAP × 1000) + 30000`
  ms.
- Run it in the foreground — don't proactively background it.
- Escalate only if the Bash tool's timeout actually kills the call: re-run
  the exact same command once with `run_in_background: true` and the full
  `RC_REVIEWER_TIMEOUT=<reviewer_timeout_seconds>` (uncapped).
- A result returned by the foreground attempt (including a `SKIPPED`) is
  final — don't re-run just because the configured cap exceeds 570s.

**Verdict handling.** Give the verifier only each finding's claim and the
relevant file/lines — never review-pr's reasoning. Ask for UPHELD / REFUTED
(must cite counter-evidence) / INCONCLUSIVE.

- A `SKIPPED` result (soft or hard) is treated the same as INCONCLUSIVE —
  tag `[unverified]`, never REFUTED — absence of a verdict is never positive
  counter-evidence.
- **Drop only on REFUTED.** A REFUTED finding is removed from the main
  severity sections but never vanishes silently: record it in a
  "Refuted During Cross-Check" subsection in the final report (Step 8),
  naming the finding and the verifier's cited counter-evidence. "Drop"
  always means "moved and explained," never "disappeared."
- **UPHELD** tags the finding `[cross-checked]` — deliberately distinct from
  review-council's own `[cross-reviewed]` badge, since this is one ad hoc
  verifier call, not review-council's full lens/refutation/judge pipeline.
- **INCONCLUSIVE**, and every skipped SUGGESTION-tier finding, is tagged
  `[unverified]` — not `[1 reviewer · unverified]`. Per review-council's own
  Step 5.3 semantics, `[1 reviewer · unverified]` means "no other family
  exists to check against"; Step 6 is only ever reached after the
  ≥2-repo-capable-family gate has already passed, so that badge would
  overstate the limitation here.

## Step 7 — Degraded-mode report

If Pass B never ran, or started but didn't finish, tag every finding
`[1 reviewer · unverified — <reason>]`, where `<reason>` reflects the actual
cause:

- `no independent model available` — plugin absent or gate not satisfied.
- `Pass B skipped: no resolvable target for committed-branch review` — the
  Step 1 known-limitation scenario (a model was available, but
  review-council couldn't resolve a target).
- `Pass B invocation failed: <review-council's own abort reason>` — the gate
  passed and a target resolved, but review-council's own run aborted
  mid-execution.

In all three cases, report Pass A's already-complete results via this path —
never discard them because Pass B didn't finish. State the specific
limitation in the report header up front — never a generic reason that
doesn't match what actually happened.

## Step 8 — Final report

Reuse review-pr's existing Output Style near-verbatim:

- Severity summary table (CRITICAL / WARNING / SUGGESTION counts).
- Per finding: exact file + line, a short paste-ready review comment, and a
  GitHub `/pull/<n>/changes#diff-<sha256>R<line>` deep-link for PR targets
  (file:line reference for file/plan targets).
- "What's done well" (brief).
- Approval recommendation (Request Changes / Approve with comments /
  Approve) — only for PR/branch targets, matching review-pr's own scope for
  this section.
- Each finding shows its corroboration badge where one applies.

**Council-only findings don't arrive in this shape natively** —
review-council emits `location`/`issue`/`recommendation`, not a paste-ready
comment or deep-link. Synthesize both for every council-only finding using
review-pr's own conventions, so the merged report is uniformly formatted,
never two-tier.

**Badge legend** — print one, covering every badge that actually appears in
this report: `[verified]`, `[cross-reviewed]`, `[cross-checked]`,
`[1 reviewer · unverified]`, `[unverified]`, `[tool-only:<rule>]`. No badge
may appear unexplained; `[cross-checked]` in particular needs its own
definition (one ad hoc cross-model verifier call via Step 6) since it's new,
not one of review-council's native badges.

**Refuted During Cross-Check** — if Step 6 refuted any review-pr-only
finding, include this subsection listing the finding and the verifier's
counter-evidence, rather than omitting refuted findings without a trace.

## Step 9 — Hard rules (carried over verbatim from review-pr)

- Never auto-open a PR or post comments — the user does that manually.
- Jira access is read-only via `acli`. If a write would be needed, say so
  and let the user do it manually.
- Always state that this skill was used, and which passes actually ran.
