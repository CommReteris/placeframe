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
         "checkout_ref": { "abc123": ["path/to/file_at_that_commit"] },
         "rename": { "old/path/file.md": "new/path/file.md" },
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
   - `checkout`: Files or directories to `git checkout $BACKUP -- <files>`. Auto-staged by git. This covers most cases. **Every path must exist in the backup** — verify with the file analysis from step 2. Accepts directory pathspecs (e.g. `"src/module/"`) — git will restore all files under that directory. All paths are passed in a single command.
   - `checkout_ref`: Dict of commit ref → list of file paths. Runs `git checkout <ref> -- <files>` for each ref. Use when a file's desired intermediate state matches a prior commit on the branch — avoids embedding full file content in the plan. The commit hashes come from the `git log` analysis in step 2.
   - `rename`: Dict of old path → new path. Implicitly checks out the old path from the backup, creates parent directories, then runs `git mv`. Prefer over `checkout`+`delete` pairs for pure renames (same content, different path). Fall back to `checkout`+`delete` only when the rename also involves content changes.
   - `delete`: Files to `git rm`. Use for deletions. Append a trailing `/` to a path (e.g. `"old/directory/"`) to trigger recursive deletion (`git rm -r`).
   - `content`: Dict of filepath → literal file content string. Use for partial file splits where a file's changes need to appear in different commits (see step 5). The wrapper writes the content and runs `git add`. Prefer `checkout_ref` when the desired state matches a prior commit.
   - Each commit must have at least one of `checkout`, `checkout_ref`, `rename`, `delete`, or `content`.

   - **Do NOT include `tidy-commits.json` in any of the new commits.** It's a temporary artifact, not project code.

5. **Handle partial file splits (if needed):**
   - Sometimes a single file has changes belonging to different logical commits.
   - **Prefer `checkout_ref`** when the desired intermediate state matches a prior commit on the branch. Use the commit hash from your `git log` analysis: `"checkout_ref": {"<hash>": ["config.py"]}`.
   - Fall back to `content` when the intermediate state doesn't correspond to any single commit (e.g. a hand-crafted blend of changes).
   - For the final commit that includes the file's ultimate state, use `checkout` to pull the final version from the backup.
   - Example: if `config.py` has both a refactor change and a feature change, and the refactor was introduced in commit `abc123`, the refactor commit uses `"checkout_ref": {"abc123": ["config.py"]}` and the feature commit uses `"checkout": ["config.py"]`.

6. **Run the wrapper** immediately after writing the plan: `uv run tidy-commits-wrapper`. Pass `--base <ref>` to override base detection (useful when the auto-detected base is wrong, e.g. after a force-push or when tidying from an arbitrary ancestor). Then report the result.

## Important rules

- NEVER use `git rebase -i` — it requires interactive input. Instead, the plan builds commits from scratch on a new branch.
- NEVER force-push or delete branches without explicit user approval.
- NEVER delete backup branches. The wrapper auto-numbers them (`-backup`, `-backup-2`, etc.) when previous backups exist.
- NEVER modify commits on main.
- If the branch has only 1 commit already, ask the user if they still want to proceed.
- **File renames**: Prefer the `rename` field for pure renames (same content, different path). Fall back to `checkout`+`delete` only when the rename also involves content changes. Check `git diff <base>..HEAD --stat` for renames.

## Large-scale reorganizations

When the branch has hundreds of commits or 1000+ changed files, manual JSON construction isn't feasible. Use programmatic plan generation instead:

- **Directory pathspecs**: Use directory paths in `checkout` (e.g. `"src/module/"`) to restore entire subtrees in one entry instead of listing every file.
- **Recursive delete**: Use trailing `/` in `delete` paths (e.g. `"old/directory/"`) to recursively remove directories.
- **`--base` override**: If the auto-detected base is wrong (common after force-pushes or unusual branch topologies), pass `--base <ref>` to `uv run tidy-commits-wrapper`.
- **Programmatic plan building**: Write a script or use Claude to generate the JSON plan programmatically from `git log` / `git diff` output. The plan schema is simple enough for code generation. Validate with `TidyCommitsPlan.model_validate_json()` before running the wrapper.
