---
id: T35
title: Add empty-diff early exit to commit skill
status: ready
depends_on: []
---

# T35: Add empty-diff early exit to commit skill

## Goal

Exit early with a clear message when there's nothing to commit, instead of running through all steps and failing.

## Context

If the user runs `/commit` with no staged or unstaged changes, the skill currently runs through all 7 steps (reading style guide, running git diff, etc.) before failing at `git commit`. A quick check at the start would save time.

## Key files

- `.claude/skills/commit/SKILL.md`

## Approach

Add to step 2: after running `git status`, if there are no staged changes and no unstaged modifications and no untracked files, say "Nothing to commit" and stop.

## Done when

- Commit skill exits early with a clear message when there's nothing to commit
