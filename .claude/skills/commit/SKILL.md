---
name: commit
description: Stage and commit current changes with a well-crafted message. Smarter replacement for quick WIP commits — actually reads diffs to write accurate messages.
---

Create a git commit of current changes with a clear, accurate commit message. If the user provided arguments (e.g. `/commit T4 branch strategy`), use them as hints for the message. Follow these steps:

1. **Read the style guide**: Read `.claude/skills/shared/commit-style.md` for commit message conventions.

2. **Understand the changes**: Run `git status` and `git diff` (staged and unstaged) to see exactly what changed. Read specific files if the diff alone isn't clear enough to write an accurate message.

3. **Stage files**: Stage modified and untracked files by name — **never use `git add .` or `git add -A`**. Skip `.env`, credentials, secrets, and other files that should not be committed.

4. **Write the commit message**: Following the style guide, write a subject line and optional body that accurately describes what changed. Use any user-provided hints to inform the message, but always ground it in the actual diff.

5. **Commit**: Create the commit using a heredoc for the message. Do NOT add Co-Authored-By or other trailers.
   ```
   git commit -m "$(cat <<'EOF'
   Subject line here

   - Body bullet if needed
   EOF
   )"
   ```

6. **Show the result**: Run `git log -1` to display the new commit.
