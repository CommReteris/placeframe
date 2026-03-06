# Permission Strategy

**Threat model**: Zero trust of Claude's output. Assume Claude can produce literally any string. The only concern is unapproved changes to the repo — this is FOSS, there are no secrets.

**Pre-approval chain**: Every file change reaches disk through an Edit or Write tool call the user already approved. By the time a skill like `/commit` runs, all dirty files are pre-approved content. The only unapproved artifact is the one the skill creates (a commit message, a script).

**One gate per skill**: Each skill should have exactly one prompted tool call — the one where the user reviews the skill's output. Everything else (reads, staging, cleanup) should be auto-allowed. Examples:
- `/commit`: gate = `git commit` (user reviews the message)
- `/tidy-commits`: gate = `Write(tidy-commits.json)` (user reviews the plan)

**Consequence**: `git add` is safe to auto-allow — it only stages pre-approved content. The commit is the gate. Write commands that are mechanical steps *after* an approval gate (like `uv run tidy-commits-wrapper` running an already-approved script) are also safe.
