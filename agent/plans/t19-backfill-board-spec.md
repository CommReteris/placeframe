---
id: T19
title: Backfill board app specification
status: plan-needed
depends_on: [T18]
---

# T19: Backfill board app specification

## Goal

Create the first SPEC.md for the kanban board app using the backfill workflow established in T18, producing a living behavioral specification that captures what was actually built including post-implementation refinements.

## Context

The board was implemented under T16 before the spec convention existed. Most implementation context is recoverable from the current codebase and recent development history. This ticket serves as the first real exercise of the backfill workflow and as the reference example for T21 (backfill all other subsystems).

The board's current behavior includes: 5-column kanban layout (blocked → design-needed → plan-needed → ready → done), card content (id, title, dependency count), drag-to-move with PATCH persistence and page invalidation, resizable detail drawer (320px minimum, left-edge handle, pointer capture), markdown body rendering via `marked`, client-side search by id/title, dark theme with OKLCH status colors, and Svelte 5 runes for state management.

## Key files

- `apps/sveltekit/board/SPEC.md` — the deliverable

## Approach

To be written during plan mode. Will follow the backfill process defined in `.claude/skills/shared/spec-backfill.md`.

## Done when

### Verifiable now
- `apps/sveltekit/board/SPEC.md` exists
- Spec follows the format defined in `.claude/skills/shared/spec-format.md`
- Spec covers all current board behavior (columns, cards, drag-and-drop, detail panel, search, styling)
- Spec documents key design decisions (library choices, state management approach, filesystem backend)

### Requires manual verification
- Spec accurately reflects user intent, not just what the code happens to do
- Spec is detailed enough that the board could be rebuilt from it without repeating the original design deficiencies
- User has explicitly approved all spec content
