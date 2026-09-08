---
name: review-pr
description: Performs a detailed review of either a pull-request or a local branch which is planed to become a PR.
---
# Review PR
## Instructions
Conduct a comprehensive, in-depth code review for the request, prioritizing quality over speed.

Think deeply step-by-step before responding.
Reference similar past PRs if relevant.

If review of local commit or branch before opening a PR is requested, compare changes against remote upstream main branch.

Challenge all your findings to avoid falsy output.

### Severity classification

Tag every finding as **CRITICAL**, **WARNING**, or **SUGGESTION**:
- **CRITICAL** — bugs, security holes, data-loss risks, or correctness failures that must be fixed before merge.
- **WARNING** — maintainability, readability, or convention issues that should be addressed but do not block merge alone.
- **SUGGESTION** — optional improvements, style nits, or future-proofing ideas.

When uncertain, prefer SUGGESTION over WARNING, WARNING over CRITICAL.

### Core Focus Areas:
- Bugs & Risks: Scrutinize for bugs, potential edge cases, and subtle issues that could arise in production.

- Maintainability & Scalability: Assess code structure for long-term ease of updates, refactoring, and extension.

- Clarity & Readability: Ensure code is intuitive and well-documented for onboarding new developers.

- Standards & Consistency: Enforce project-specific style guides, naming conventions, and best practices.

- Security: Identify vulnerabilities like injection risks, auth flaws, data exposure, or unsafe dependencies. But do not be limited to just those.

- Testing: Evaluate test suite for completeness, coverage (aim for high branch/statement metrics), relevance, and edge-case handling.

- Completeness: List all missing relevant areas not covered by the changes.

- Cross-file coherence: Verify that names, enums, types, config keys, and API contracts introduced or changed in one file are identically propagated to all other files in the project. Flag drift between siblings (e.g. a renamed constant in one file but the old name in another). Challenge yourself to avoid false-positive findings.

- Effectivity: Analyze, if any part be optimized in terms of memory, CPU or other resources usage?

- Minimal change: Is the suggested change minimal in terms of lines of affected code? Can the proposed solution be simplified??

- Reusability: Find any parts which can be reused - within this PR or with other already existing code.

- Other comments: Assess the accuracy and relevance of comments from other reviewers, suggest next steps if relevant.

- Future development: Suggest future functionality to develop related on the proposed changes and will be benefitial to the project.

- Review comments so far: evaluate if and how existing review comments were addressed.

- Convention grounding: Discover project convention docs at repo root (`CONTRIBUTING.md`, `CLAUDE.md`, `AGENTS.md`, `.editorconfig`) and check the PR against their rules. Do not invent project-specific rules - load them.

### Output Style:
- Open the review with a severity summary table so the reader can triage at a glance:

  | Severity   | Count |
  | ---------- | ----- |
  | CRITICAL   | N     |
  | WARNING    | N     |
  | SUGGESTION | N     |

- Provide clear, prioritized feedback with specific line references.

- For each issue, suggest concrete fixes or improvements (e.g., "Refactor this loop to use map() for better readability: [code snippet]").

- For each issue, also provide: exact filename, row number, and a short paste-ready review comment. Prefer a clickable link that opens the right place so the user can paste the comment (or edit the file) without hunting.

- Highlight strengths to balance critique.

- If any part of the review could not be completed (files inaccessible, diff too large to fully parse, ambiguous scope), state that explicitly. Never silently skip areas or imply a clean review when coverage was partial.

#### GitHub PR comment deep-links

When reviewing a remote GitHub PR, every finding MUST include a Files/Changes deep-link to the exact file and line (so the user can open it and paste an inline comment). Do this up front — do not wait for the user to ask.

URL form (prefer `/changes`; `/files` is an equivalent fallback if the anchor does not scroll):

```
https://github.com/<owner>/<repo>/pull/<number>/changes#diff-<pathSha256>R<line>
```

- `<pathSha256>`: SHA-256 (lowercase hex) of the PR file path exactly as in `gh api repos/<owner>/<repo>/pulls/<number>/files` → `filename` (UTF-8, no trailing newline). Example: `python3 -c "import hashlib; print(hashlib.sha256(b'path/to/file.md').hexdigest())"`. Batch: hash each `filename` from that API. Never guess the hash; never use blob URLs as the primary “leave a comment here” target.
- `<line>`: line number in the **new** file (right-hand / `+` side). Verify against PR head content. For multi-line issues, link the most representative line; mention sibling files/lines in the comment body.

Cross-repo (fork) PRs: if `isCrossRepository` is true, `blob/<headRefName>/…` on the upstream repo often 404s. Still use `/pull/<number>/changes#diff-…R…` on the upstream PR for comment targets.

Per finding emit: severity + title, one primary `#diff-…R…` link, a fenced paste-ready comment, optional related deep-links.

#### Approval recommendation

Close the review with an explicit recommendation:
- Any CRITICAL findings remaining: **"Request Changes"**
- WARNINGs only, no CRITICALs: **"Approve with comments"**
- Clean (suggestions only or none): **"Approve"**

### Extra
If you have decided to use this skill, always mention that fact in your output.

NEVER OPEN a PR or send comments automatically. The user wants to do that manually for a better control.

If you need Jira access, ALWAYS do it read-only. Never update anything remotely. If write is needed, let the user clearly know and he will do it manually.

To access Jira, use acli which authentication is in ~/.config/acli
