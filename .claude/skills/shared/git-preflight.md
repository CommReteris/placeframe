# Git Pre-flight Checks

Run these checks before any skill that creates or reorganizes commits. If any check fails, tell the user what state git is in and stop.

## Checks

1. **In-progress operation**: Run `git status`. If the output mentions a rebase, merge, or cherry-pick in progress (e.g. "interactive rebase in progress", "You have unmerged paths", "cherry-pick in progress"), abort.

2. **Detached HEAD**: Run `git branch --show-current`. If the output is empty, the HEAD is detached — abort.

3. **Uncommitted changes** (tidy-commits only): If there are staged or unstaged changes, ask the user to commit or stash them first. This does not apply to the commit skill, which exists to commit those changes.
