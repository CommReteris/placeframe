---
name: wip
description: Create a quick git commit with a short message. Use when the user asks to commit changes.
---

Create a git commit of all current changes. Follow these steps:

1. Run `git status` and `git diff` to see what changed.
2. Stage all modified and untracked files (except `.env`, credentials, or secrets).
3. Write a **very short** commit message (one line, under 50 chars). This is a working branch — commits will be squashed later. The message just needs to be recognizable at a glance.
4. Commit with the short message. Do NOT add a Co-Authored-By line.
5. Show the result with `git log --oneline -1`.
