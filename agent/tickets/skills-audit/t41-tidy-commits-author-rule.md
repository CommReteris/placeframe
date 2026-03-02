---
id: T41
title: Simplify author preservation rule in tidy-commits
status: done
depends_on: []
---

# T41: Simplify author preservation rule in tidy-commits

## Goal

Replace the ambiguous author preservation rule with a single clear rule.

## Context

The tidy-commits skill says: "When a new commit merges multiple original commits, use the author from the earliest one (or the most common one if they differ)." This gives two options without a tiebreaker, which can produce inconsistent results across sessions.

## Key files

- `.claude/skills/tidy-commits/SKILL.md` — step 4 field reference, author bullet

## Approach

Simplify to: "When merging multiple original commits, use the author from the earliest."

## Done when

- Author preservation rule has one unambiguous instruction
