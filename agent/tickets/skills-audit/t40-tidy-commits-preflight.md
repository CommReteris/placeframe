---
id: T40
title: Move uncommitted-changes check to step 0 in tidy-commits
status: done
depends_on: []
---

# T40: Move uncommitted-changes check to step 0 in tidy-commits

## Goal

Check for uncommitted changes before doing any analysis work, not at the end in the Important Rules section.

## Context

The tidy-commits skill's "if there are uncommitted changes, ask the user to commit or stash" rule is buried in the Important Rules section at the bottom. By step 4 (writing the JSON plan), the skill has already invested significant analysis work. If the check fails at that point, all that work is wasted.

## Key files

- `.claude/skills/tidy-commits/SKILL.md`

## Approach

Add step 0 before "Determine the base": run `git status`, check for uncommitted changes, abort early if found. Remove the duplicate rule from Important Rules.

## Done when

- Uncommitted-changes check happens before any analysis
- The redundant rule in Important Rules is removed
