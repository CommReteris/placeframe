---
name: tidy-commits
description: Reorganize commits on the current branch into clean, logical commits for PR review. Use when the user wants to clean up history before merging.
---

Reorganize the commits on the current branch into clean, logical commits suitable for PR review. Follow these steps:

0. **Pre-flight**: Run the checks in `.claude/skills/shared/git-preflight.md`. Stop if any fail.

1. **Determine the base:**
   - Check if `origin/<current-branch>` exists (`git rev-parse --verify origin/<branch>`). If so, use it directly as `<base>` — this limits tidying to unpushed commits only, preventing history rewrites that would require a force push.
   - If the branch hasn't been pushed yet, fall back to `git merge-base origin/main HEAD` (or `git merge-base main HEAD` if `origin/main` doesn't exist).

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

4. **Write the commit plan:**
   - First, **delete any existing `tidy-commits.json`** using the Bash tool (`rm -f tidy-commits.json`) so the user sees the new plan cleanly instead of a meaningless diff against an old version.
   - Then use the Write tool to create a fresh `tidy-commits.json` in the repo root.
   - The wrapper script (`uv run tidy-commits-wrapper`) handles backup, invariance checking, and rollback. The plan only declares commits.
   - Read authors during analysis with `git log --format="%an <%ae>" <base>..HEAD`.

   **JSON schema:**
   ```json
   {
     "committer": { "name": "Full Name", "email": "email@example.com" },
     "commits": [
       {
         "message": "Subject line\n\n- Body bullet",
         "author": "Full Name <email@example.com>",
         "checkout": ["path/to/file"],
         "delete": ["path/to/old_file"],
         "content": { "path/to/partial_file": "full intermediate content" }
       }
     ]
   }
   ```

   **Field reference:**
   - `committer`: Sets `GIT_COMMITTER_NAME` and `GIT_COMMITTER_EMAIL` for all commits. Use the most common author from the branch.
   - `message`: Full commit message. Use `\n` for newlines (it's JSON).
   - `author`: Per-commit `--author` flag. When a new commit maps to a single original, use that commit's author. When merging multiple, use the earliest.
   - `checkout`: Files to `git checkout $BACKUP -- <files>`. Auto-staged by git. This covers 95% of cases. **Every path must exist in the backup** — verify with the file analysis from step 2.
   - `delete`: Files to `git rm`. Use for deletions and the old-path side of renames.
   - `content`: Dict of filepath → literal file content string. Use for partial file splits where a file's changes need to appear in different commits (see step 5). The wrapper writes the content and runs `git add`.
   - Each commit must have at least one of `checkout`, `delete`, or `content`.

   - **Preserve original commit authors**: When a new commit maps to a single original commit, use `author` with the original commit's author. When merging multiple, use the earliest.
   - **Do NOT include `tidy-commits.json` in any of the new commits.** It's a temporary artifact, not project code.
   - Do NOT present the plan for conversational review. The user reviews it when the Write tool prompts for approval.

5. **Handle partial file splits (if needed):**
   - Sometimes a single file has changes belonging to different logical commits. Use the `content` field for this.
   - For the earlier commit(s), set `content` to the file's intermediate state (the full file content as it should exist at that point in history).
   - For the final commit that includes the file's ultimate state, use `checkout` to pull the final version from the backup.
   - Example: if `config.py` has both a refactor change and a feature change, the refactor commit uses `"content": {"config.py": "...refactored version..."}` and the feature commit uses `"checkout": ["config.py"]`.

6. **Run the wrapper** immediately after writing the plan: `uv run tidy-commits-wrapper`. Then report the result.

## Important rules

- NEVER use `git rebase -i` — it requires interactive input. Instead, the plan builds commits from scratch on a new branch.
- NEVER force-push or delete branches without explicit user approval.
- NEVER delete backup branches. The wrapper auto-numbers them (`-backup`, `-backup-2`, etc.) when previous backups exist.
- NEVER modify commits on main.
- If the branch has only 1 commit already, ask the user if they still want to proceed.
- **File renames**: When original commits renamed files (e.g., `a.md` → `b.md`), use `delete` for the old filename in the same commit that checks out the new filename. Check `git diff <base>..HEAD --stat` for renames.
