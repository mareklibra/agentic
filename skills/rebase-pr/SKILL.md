---
name: rebase-pr
description: Rebase current branch onto target branch (default: upstream/main)
---

# Rebase PR or Branch

Performs a safe rebase of the current branch onto a target branch using `git rebase`.

## Instructions

Rebase commits from the current working branch onto a target branch (default: `upstream/main` or `upstream/master`).

**Important**: Always ask for clarification if:
- The target branch is unclear
- There are merge conflicts requiring resolution decisions
- Any step fails or produces unexpected results

### Steps

1. **Pre-flight checks**
   - Check for uncommitted changes via `git status`
   - If uncommitted changes exist: inform user and STOP (do not continue)
   - Identify the current branch name
   - Determine target branch (ask user if unclear)

2. **Do a backup**
   - Create a backup branch using `git checkout -b <current-branch>.rebase_<date>` , where the `<date>` is in YYMMDD.HHmm format (Year, Month, Day, Hour, Minute)
   - Never modify the backup branch.

3. **Show what will be rebased**
   - Fetch latest changes: `git fetch --all`
   - Show commits that will be rebased using `git log <target-branch>..HEAD`
   - Display commit count, hashes, and messages
   - Give user a chance to review before proceeding

4. **Perform the rebase**
   - Run: `git rebase <target-branch>` (e.g., `git rebase upstream/main`)
   - If rebase succeeds without conflicts: proceed to Output
   - If conflicts occur: go to step 4

5. **Handle conflicts** (only if they occur)
   - Show conflicting files via `git status`
   - For each conflicting file:
     - Read and show the conflict markers
     - Explain what each side changed
     - Ask user how to resolve (or resolve if obvious)
   - After resolving conflicts:
     - Stage resolved files: `git add <files>`
     - Continue rebase: `git rebase --continue`
   - Repeat until rebase completes

6. **If rebase fails or user wants to abort**
   - Run: `git rebase --abort`
   - Inform user that branch is back to original state

### Output

Provide a summary:
- ✅ Branch: `<branch-name>`
- ✅ Rebased onto: `<target-branch>`
- ✅ Commits rebased: `N commits` (list with hashes and messages)
- ✅ New HEAD: `<hash> - <message>`

If conflicts occurred:
- 🔀 Conflicts resolved in: `<file1>`, `<file2>`, etc.
- 📝 Resolution summary: Brief explanation of changes and reasoning

If issues occurred:
- ⚠️ Issues: List any problems or concerns
- 💡 Suggestion: Next steps or recommendations

## Extra
If you have decided to use this skill, always mention that fact in your output.

NEVER OPEN a PR or do a write modification on the remote from the cursor. The user wants to do that manually for better control.

