---
id: T30
title: Add conflict resolution guidance to backfill-spec
status: ready
depends_on: []
---

# T30: Add conflict resolution guidance to backfill-spec

## Goal

Add explicit guidance for what to do when information sources disagree during spec backfill.

## Context

backfill-spec step 1 says "the code is the source of truth for behavior, and the user is the source of truth for intent." But there's no guidance for when the code contradicts a ticket, or when the user's stated intent contradicts what the code does. Without explicit conflict resolution, the skill may silently pick the wrong source.

## Key files

- `.claude/skills/backfill-spec/SKILL.md` — step 1

## Approach

Add to step 1: "If code and ticket disagree, note the discrepancy and ask the user which is correct."

## Done when

- Step 1 has explicit conflict resolution guidance for code vs ticket and code vs user intent disagreements
