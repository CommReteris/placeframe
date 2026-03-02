---
id: T47
title: Create shared git pre-flight check reference
status: done
depends_on: []
---

# T47: Create shared git pre-flight check reference

## Goal

Create a shared reference file for git state checks that multiple skills need before starting.

## Context

Both commit (T34) and tidy-commits (T40) need to check for unusual git states before proceeding (mid-rebase, mid-merge, uncommitted changes). Rather than duplicating this logic in each skill, a shared reference file lets skills point to one place.

## Key files

- `.claude/skills/shared/` — new file: `git-preflight.md`
- `.claude/skills/commit/SKILL.md` — would reference it
- `.claude/skills/tidy-commits/SKILL.md` — would reference it

## Approach

Create `.claude/skills/shared/git-preflight.md` covering: check for mid-rebase/merge/cherry-pick state, check for uncommitted changes, check for detached HEAD. Skills reference it as a step 0.

## Done when

- Shared git-preflight.md exists with the common checks
- commit and tidy-commits skills reference it instead of duplicating the logic
