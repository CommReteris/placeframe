---
id: T28
title: Add fallback guidance to allow-tool classification lists
status: ready
depends_on: []
---

# T28: Add fallback guidance to allow-tool classification lists

## Goal

Add a note to the allow-tool skill's classification step so it handles commands that don't fit any existing category instead of silently misclassifying them.

## Context

The allow-tool skill has hardcoded lists of read-only, pre-approved, and unapproved commands. As the project adds new tools (pnpm, npx, etc.), these lists go stale. Currently there's no guidance for what to do when a command doesn't match any category.

## Key files

- `.claude/skills/allow-tool/SKILL.md` — step 2 classification lists

## Approach

Add a fallback clause after the three categories: "If the command doesn't clearly fit any category, ask the user how they want it classified."

## Done when

- Step 2 in allow-tool SKILL.md has a fallback clause for unrecognized commands
