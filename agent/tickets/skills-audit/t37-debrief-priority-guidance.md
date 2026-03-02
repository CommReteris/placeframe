---
id: T37
title: Add priority guidance to debrief skill
status: done
depends_on: []
---

# T37: Add priority guidance to debrief skill

## Goal

Add a suggested priority order for uncaptured items so the user can triage efficiently.

## Context

When debrief surfaces many uncaptured items, the user has to evaluate each one without guidance on what matters most. A suggested priority order helps focus on the highest-value items first.

## Key files

- `.claude/skills/debrief/SKILL.md` — step 2

## Approach

Add to step 2: "Present items in rough priority order: decisions about how the project works > identified gaps or problems > future work ideas > user preferences > open threads."

## Done when

- Step 2 specifies a priority order for presenting uncaptured items
