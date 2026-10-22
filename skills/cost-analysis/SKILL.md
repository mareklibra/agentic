---
name: cost-analysis
description: Retrospective on the current agent session's token usage, with concrete suggestions to cut cost or move steps to cheaper models next time. Use when the user asks for a cost review, token-usage analysis or retrospective, "why was this session expensive", or how to make the same task cheaper on a re-run.
---
# Agent session cost analysis

Look back at the session and recommend where the same or a similar task could be cheaper next time. Keep the analysis itself cheap: do not re-read large files you already saw, and keep the whole output within about one screen.

## 1. Gather evidence

1. Understand the motivation of the run, which skills were used and how, which subagents were spawned, and which pulled-in data (file reads, tool output, loaded skill text) was actually used and which was waste.
2. Measure if possible. Take the newest `.jsonl` under `~/.claude/projects/<encoded-cwd>/` as the current session (ask only if that is ambiguous) and run:

   `python3 -I <this-skill-dir>/scripts/session-usage.py <transcript.jsonl>`

   It sums the main transcript plus all subagent transcripts, per transcript and per model. The weights are a ratio model, not a bill. A session ID or transcript path as the skill argument selects a past session instead.
3. With no transcript (another tool, no access), analyze qualitatively and say plainly that nothing was measured.

## 2. Output

**Findings**: the motivation in one line, the top 3 token sinks (from the numbers when measured), and what was used versus wasted.

**Recommendations**, ranked by estimated saving. Each one is `file → change → why it saves tokens`, labelled *measured* or *guessed*. Name the exact place and pick the best-fitting level: AGENTS.md/CLAUDE.md, README or docs, a skill, a script, on the project or the global level.

**Model tiers**: for each step that could run cheaper, name the tier and the reason, using vendor-neutral tiers: smallest/fastest, mid, most capable (in Claude, for example, Haiku/Sonnet/Opus). Mechanical, verifiable work such as lookups, file searches and formatting fits a smaller tier or a subagent. Also flag delegation that cost more than it saved.

Never suggest a saving that trades away correctness, such as dropping review rounds. Propose a cheaper model only for steps whose output can be verified.

## 3. Follow-up

Do not edit anything. Offer to run a `plan-and-review` session that addresses the recommended changes.
