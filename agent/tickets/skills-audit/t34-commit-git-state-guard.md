---
id: T34
title: Add git state pre-flight check to commit skill
status: done
depends_on: []
---

# T34: Add git state pre-flight check to commit skill

## Goal

Check for unusual git states (mid-rebase, mid-merge, mid-cherry-pick) before starting the commit flow.

## Context

If the user runs `/commit` while git is in a rebase or merge state, `git commit` behaves unexpectedly (may finalize a merge commit, or fail in confusing ways). The skill currently has no guard for this.

## Key files

- `.claude/skills/commit/SKILL.md`

## Approach

Add step 0: run `git status` and check for indicators of rebase/merge/cherry-pick state. If detected, inform the user and abort.

## Done when

- Commit skill detects mid-rebase, mid-merge, and mid-cherry-pick states
- Skill informs the user and stops instead of proceeding
