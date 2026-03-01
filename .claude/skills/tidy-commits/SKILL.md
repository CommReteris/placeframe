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
   - **Never put prose files and code files in the same commit.** Prose files are markdown, text, skill files, and research notes. Code files are Python, configs, .gitignore, pyproject.toml. If a logical change spans both (e.g. a new feature + its SKILL.md), split into two commits.
   - Read `.claude/skills/shared/commit-style.md` for commit message conventions.
   - Write a clear commit message for each planned commit following the style guide.
   - Do NOT present the plan for conversational approval — the Write tool permission prompt is the gate.

4. **Write the commit-building script:**
   - First, **delete any existing `tidy-commits.sh`** using the Bash tool (`rm -f tidy-commits.sh`) so the user sees the new script cleanly instead of a meaningless diff against an old version.
   - Then use the Write tool to create a fresh `tidy-commits.sh` in the repo root.
   - The wrapper script (`uv run tidy-commits-wrapper`) handles backup, invariance checking, and rollback. The generated script only builds commits. It receives three environment variables from the wrapper: `$BRANCH`, `$BASE`, and `$BACKUP`. Use these — do NOT compute them.
   - The script should:
     - `set -euo pipefail` for safety
     - Build new commits on a **temporary branch** (e.g. `${BRANCH}-tmp`) starting from `$BASE`
     - Use `git checkout $BACKUP -- <files>` to pull files from the backup. **NEVER use `git add -A` or `git add .`** — these will pick up untracked files (like the script itself). Instead, `git checkout ... -- <files>` already stages the files, so just run `git commit` directly without a separate add step.
     - **Preserve original commit authors**: When a new commit maps to a single original commit, use `--author="Name <email>"` with the original commit's author. When a new commit merges multiple original commits, use the author from the earliest one (or the most common one if they differ). Read authors during analysis with `git log --format="%an <%ae>" <base>..HEAD`.
     - **Set committer identity explicitly**: Export `GIT_COMMITTER_NAME` and `GIT_COMMITTER_EMAIL` at the top of the script to match the author. Environment variables (e.g. from a container) can override `git config`, so always set these explicitly.
     - On success, move the **original branch name** to the new commits: `git branch -f $BRANCH ${BRANCH}-tmp`
     - Switch back to the original branch: `git checkout $BRANCH`
     - Delete the temp branch: `git branch -d ${BRANCH}-tmp`
   - **Do NOT create a backup branch** — the wrapper handles this.
   - **Do NOT verify tree invariance** — the wrapper handles this.
   - **Do NOT include `tidy-commits.sh` in any of the new commits.** It's a temporary utility, not project code.
   - Do NOT present the script for conversational review. The user reviews it when the Write tool prompts for approval.

5. **Handle partial file splits (if needed):**
   - Sometimes a single file has changes belonging to different logical commits. This requires generating patches and applying specific hunks — which is fragile and hard to review in a script.
   - **We don't have a reliable automated approach for this yet.** If the plan requires splitting a file across commits, flag this to the user and discuss how to handle it before writing the script.

6. **Run the wrapper** immediately after writing the script: `uv run tidy-commits-wrapper`. Then report the result.

## Important rules

- NEVER use `git rebase -i` — it requires interactive input. Instead, build commits from scratch on a new branch.
- NEVER use `$()` command substitution or `for` loops over git output in Bash commands — these trigger permission prompts every time. Use single git commands (e.g., `git log --reverse --oneline --name-only`) instead.
- NEVER force-push or delete branches without explicit user approval.
- NEVER delete backup branches. The wrapper auto-numbers them (`-backup`, `-backup-2`, etc.) when previous backups exist.
- NEVER modify commits on main.
- If there are uncommitted changes, ask the user to commit or stash them first.
- If the branch has only 1 commit already, ask the user if they still want to proceed.
- **File renames**: When original commits renamed files (e.g., `a.md` → `b.md`), the script must `git rm` the old filename in the same commit that checks out the new filename. Check `git diff <base>..HEAD --stat` for renames.
