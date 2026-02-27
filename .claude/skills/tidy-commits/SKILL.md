---
name: tidy-commits
description: Reorganize commits on the current branch into clean, logical commits for PR review. Use when the user wants to clean up history before merging.
---

Reorganize the commits on the current branch into clean, logical commits suitable for PR review. Follow these steps:

1. **Determine the base:**
   - Run `git merge-base origin/main HEAD` to find the true fork point. Use this as `<base>` throughout.
   - If `origin/main` doesn't exist, fall back to `git merge-base main HEAD`.

2. **Analyze the current state:**
   - Run `git log --oneline <base>..HEAD` to see all commits on this branch.
   - Run `git diff <base>..HEAD --stat` to see the full set of changed files.
   - Run `git log --reverse --oneline --name-only <base>..HEAD` to see which files changed in each commit.
   - For files that need closer inspection, use the Read tool or `git diff <base>..HEAD -- <path>`.

3. **Plan the new commit structure:**
   - Read through all the changes and group them into logical, self-contained commits.
   - Each commit should represent one coherent change (a feature, a fix, a refactor, a config change, etc.).
   - Order commits so that earlier commits don't depend on later ones.
   - Write a clear commit message for each planned commit following the commit message style guide below.
   - Present the plan to the user and wait for approval before proceeding.

## Commit message style guide

- **Subject line**: Concise but specific (under 72 chars). Name the actual things that changed — don't hide details behind vague catch-alls like "update config" or "fix scripts".
- **Body**: Use a bulleted list (`-`) of short phrases. State *what* changed, not *why*. No full sentences, no parenthetical justifications.
- **Brevity**: Err heavily on the side of terse. "Fix label_type/link_type to NOT NULL" not "Fix label_type and link_type columns in nodes table to be NOT NULL (were incorrectly nullable)". "Remove openapi-generator-cli from docker/api dev deps" not "Remove openapi-generator-cli from docker/api dev dependencies — it was never used by the API service".
- **Accuracy**: Name the specific things that changed. Don't hide bug fixes under vague phrasing.
- **Structure**: Subject line summarizes the theme; bullets in the body cover specifics that wouldn't fit in the subject.

4. **Create a backup branch:**
   - Before doing anything destructive, create a backup branch as a **separate Bash tool call** so the user can see it:
     `git branch <branch>-backup`
   - This must be its own tool use — not part of the script — so the user sees "backup created" before anything else happens.

5. **Ensure `tidy-commits.sh` is gitignored:**
   - Before writing the script, add `tidy-commits.sh` to `.gitignore` (if not already there) and `git rm --cached tidy-commits.sh` if it's currently tracked.
   - This keeps the script untracked so git won't block branch switches.
   - Commit the `.gitignore` change to the current branch before running the script.

6. **Write a shell script to build the commits:**
   - First, **delete any existing `tidy-commits.sh`** using the Bash tool (`rm -f tidy-commits.sh`) so the user sees the new script cleanly instead of a meaningless diff against an old version.
   - Then use the Write tool to create a fresh `tidy-commits.sh` in the repo root.
   - The script should:
     - `set -euo pipefail` for safety
     - Build new commits on a **temporary branch** (e.g. `<branch>-tmp`) starting from `<base>`
     - Use `git checkout <backup-branch> -- <files>` to pull files from the backup (which points at the original history). **NEVER use `git add -A` or `git add .`** — these will pick up untracked files (like the script itself). Instead, `git checkout ... -- <files>` already stages the files, so just run `git commit` directly without a separate add step.
     - **Preserve original commit authors**: When a new commit maps to a single original commit, use `--author="Name <email>"` with the original commit's author. When a new commit merges multiple original commits, use the author from the earliest one (or the most common one if they differ). Read authors during analysis with `git log --format="%an <%ae>" <base>..HEAD`.
     - **Set committer identity explicitly**: Export `GIT_COMMITTER_NAME` and `GIT_COMMITTER_EMAIL` at the top of the script to match the author. Environment variables (e.g. from a container) can override `git config`, so always set these explicitly.
     - After all commits, verify: `git diff <tmp-branch> <backup-branch>` to confirm trees are identical
     - On success, move the **original branch name** to the new commits: `git branch -f <branch> <tmp-branch>`
     - Switch back to the original branch: `git checkout <branch>`
     - Delete the temp branch: `git branch -d <tmp-branch>`
     - Print the new commit log
   - **Do NOT include `tidy-commits.sh` in any of the new commits.** It's a temporary utility, not project code.
   - The end result: the user ends up on their original branch with clean history. The backup branch preserves the old history.
   - Present the script to the user for review. They approve it once, then run it.

7. **Handle partial file splits (if needed):**
   - Sometimes a single file has changes belonging to different logical commits. This requires generating patches and applying specific hunks — which is fragile and hard to review in a script.
   - **We don't have a reliable automated approach for this yet.** If the plan requires splitting a file across commits, flag this to the user and discuss how to handle it before writing the script.

8. **Run the script** after user approval, then report the result. Do NOT delete the backup branch.

## Important rules

- NEVER use `git rebase -i` — it requires interactive input. Instead, build commits from scratch on a new branch.
- NEVER use `$()` command substitution or `for` loops over git output in Bash commands — these trigger permission prompts every time. Use single git commands (e.g., `git log --reverse --oneline --name-only`) instead.
- NEVER force-push or delete branches without explicit user approval.
- NEVER modify commits on main.
- If there are uncommitted changes, ask the user to commit or stash them first.
- If the branch has only 1 commit already, ask the user if they still want to proceed.
