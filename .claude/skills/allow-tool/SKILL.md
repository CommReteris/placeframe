---
name: allow-tool
description: Add a permission rule to .claude/settings.json so a previously-prompted tool is auto-allowed in future sessions.
---

Add a permission allow rule to `.claude/settings.json`. The user just encountered a tool permission prompt they don't want to see again.

Reference: `.claude/skills/shared/permission-strategy.md` for the project's permission philosophy (threat model, pre-approval chain, one gate per skill).

## Steps

1. **Infer the rule**: Look at the conversation context — the most recent tool call that was prompted or rejected tells you what to allow. Generalize it to a useful pattern (e.g. if `git log --oneline -10` was prompted, propose `Bash(git log *)` not the exact command). If you can't confidently infer it, ask.

2. **Classify the command**: Determine which category it falls into.

   **Read-only** — safe to auto-allow:
   - File inspection: `cat`, `head`, `tail`, `less`, `wc`, `file`, `stat`, `ls`, `find`, `tree`
   - Git reads: `git log`, `git diff`, `git show`, `git status`, `git merge-base`, `git branch --list`, `git rev-parse`, `git shortlog`
   - Search: `grep`, `rg`, `ag`, `fd`
   - System info: `uname`, `whoami`, `which`, `env`, `printenv`, `docker info`, `docker ps`
   - Build/test: `uv run pytest`, `uv run ruff check`, `uv run basedpyright`

   **Pre-approved writes** — safe to auto-allow (see strategy above):
   - `git add` — only stages content already approved through Edit/Write prompts
   - Specific cleanup commands tied to a skill (e.g. `rm -f tidy-commits.json`)
   - Execution of an already-approved artifact (e.g. `uv run tidy-commits-wrapper`)

   **Unapproved writes** — must stay prompted, refuse to auto-allow:
   - File mutation: `rm`, `mv`, `cp`, `chmod`, `chown`, `mkdir`, `touch`, `tee`, redirects
   - Git write commands: `git commit`, `git push`, `git checkout`, `git reset`, `git rebase`, `git branch -d/-D/-f`, `git merge`, `git stash`, `git tag`, `git cherry-pick`
   - Package changes: `uv add`, `npm install`, `pip install`, `apt install`
   - Docker mutation: `docker run`, `docker build`, `docker compose up`, `docker compose down`
   - Process control: `kill`, `pkill`

   If the command is an unapproved write, **refuse** — tell the user why. Do not proceed to steps 3–5.

   **Unrecognized** — if the command doesn't clearly fit any category above, don't guess. Tell the user which category you think it's closest to and ask them to confirm before proceeding.

3. **Read the current settings**: Read `.claude/settings.json` to see existing permissions.

4. **Propose the rule**: Tell the user what pattern you want to add and what it will permit. Wait for their confirmation via the file edit approval — do not ask separately.

5. **Add the rule**: Add the new pattern to the `permissions.allow` array using the Edit tool. Do not remove or reorder existing entries.
