# Personal agent rules (all projects)

Applies to every repository and every tool.
`scripts/install-skills.sh` in [mareklibra/agentic](https://github.com/mareklibra/agentic) links it to `~/.config/agents/AGENTS.md`; Claude Code imports it from `~/.claude/CLAUDE.md`, Cursor reads it through a rule in `~/.cursor/rules/` (see the README).
A project's `AGENTS.md` names the project-specific parts (pre-push gate, Tier 2 areas, data hazards) and may tighten a rule here.

## Project AGENTS.md precedence

- Its Rules section wins over the README and `docs/`.
- For descriptive content (commands, layout, behavior) the code wins: fix the stale `AGENTS.md` line in the same change.

## Working style

- Plan first for any non-trivial task (3+ steps or a design decision): checkable items, validated before implementing.
- Challenge your work before presenting it; give a short high-level summary at each step.
- Simplest change that works; reuse existing code; match the surrounding code.
- Comments explain _why_ and name the doc section a rule comes from.

## Git

- Work on a topic branch; where the project says so, reach `main` only through a rebase-merged PR: never commit to local `main`, never push `origin/main`.
- If `main` moved, rebase onto `origin/main` (never merge `main` in); `--force-with-lease` only on your own branch.
- Open a PR only when asked.
- The main checkout stays on `main`.
  You are in it when `git rev-parse --path-format=absolute --git-dir` and `--git-common-dir` print the same path.
  Before the first edit: `git worktree add -b <branch> <main-checkout>/.claude/worktrees/<short-name> origin/main`, then edit only under that path.
  No `git checkout` / `git switch` in the main checkout, also when nothing is committed.
- The stash is shared by all worktrees: do not use `git stash`, use a WIP commit.

**Commit messages** (every commit, also amended and rewritten ones):

- Title: imperative, at most 80 characters (aim for about 70), no trailing period.
- Blank line, then a body hard-wrapped at 72 characters in short paragraphs that explains _why_. Never one long line.
- Check the title length and the longest body line before committing.

## Plans and scratch files

- Plan files go to `<main checkout>/.claude/plans/<name>.plan.md` (git-ignored); in a worktree the main checkout is the parent of `git rev-parse --git-common-dir`.
- A plan has a Decisions section: grill answers and rejected alternatives, no secrets.
- After a plan converges, continue in a fresh session; the plan file is the hand-off.
- Other scratch files go to the tool's scratch directory, never into tracked directories.

## Review

Review your own diff before handing over, then review by tier with the `review-pr` and `review-pr-ultra` skills. Fix or answer every finding.

- **Tier** = the highest of the touched files; a behavior change in a Tier 2 area is Tier 2 however small; when unsure go up; name the tier in the PR description.
- **Tier 0** (typos, formatting, comments that change no behavior): the gate and a self-read.
- **Tier 1** (ordinary features, docs, scripts, CI and build config): plan review at most 2 rounds; one fresh-context `review-pr` before the PR, a delta one after later fixes; `review-pr-ultra` on request.
- **Tier 2** (the project lists its areas; by default auth and security, access control, schema and migrations, data-integrity logic, process and host boundaries, code that sends secrets or user data out): as Tier 1, plus a 3rd plan round when round 2 had a CRITICAL or changed the design.
  The pre-PR `review-pr` runs on the strongest model available and its prompt contains the first-read checklist.
  Then `review-pr-ultra` once on the post-fix revision (if that `review-pr` found nothing to fix, pass it as ultra's Pass A so only the council runs).
  After later fixes, a delta `review-pr` on the strongest model; re-run the council when the fixes exceed about 30 lines or touch security or a process boundary.
- **First-read checklist** (paste into the reviewer prompt): (1) for each value that crosses a process, host or trust boundary (URLs, ports, paths, env, user input), where it is computed and what the receiving side actually sees; (2) which env/config reaches each process and with what value; (3) when a secret is sent relative to confirming the peer.
- Never repeat a review on an unchanged revision.
  Reviewers are not the author: fresh context, except a Tier 1 delta of under about 30 lines that fixes only named findings with the gate green.

## Testing

- Write or extend tests with every change; a bug fix gets a regression test; cover corner cases.
- Features at an external boundary (database, network, process spawn, third-party API) get one real-environment run of the narrowest live target.
- Security and lifecycle tests get a hand-made mutation check: break each changed line, the test must fail.
- Suites that run for many minutes: only when needed or asked.

## Data safety

- Before running anything that writes to a database (tests, seeds, resets, scripts), know which database the env points at; never at data you want to keep without asking.
- Never run two suites against the same database at once.
- Never read, print or commit secrets, backups or production dumps.

## Tool output

- Pipe commands that can be verbose (builds, test suites, `make`, always `make -pn`) through `tail -n`, `grep -E` or `awk`.
- Write the full output to a scratch file and show only the tail or the failures.
