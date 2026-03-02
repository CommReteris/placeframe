---
id: T50
title: Board UI epic grouping
status: design-needed
depends_on: []
---

# T50: Board UI epic grouping

## Goal

Add epic-aware grouping to the kanban board so that tickets organized in epic subdirectories are visually grouped in the UI.

## Context

T26 introduces epic support via subdirectories under `agent/tickets/`. The board's `tickets.ts` will be updated (as part of T26) to scan subdirectories, so the data layer will already know which epic a ticket belongs to. This ticket adds the visual layer: showing epic grouping in the board UI.

Blocked by T26 — the directory convention and data plumbing must exist first.

## Key files

- `apps/sveltekit/board/src/lib/server/tickets.ts` — ticket type needs epic field (derived from path)
- `apps/sveltekit/board/src/lib/components/Board.svelte` — layout changes for epic grouping
- `apps/sveltekit/board/src/routes/+page.svelte` — page-level epic filter or grouping toggle

## Approach

TBD — needs design discussion after T26 lands.

## Done when

- Board shows which epic each ticket belongs to (badge, color, or section)
- User can filter the board by epic
- Ungrouped tickets (at root) display without an epic label
- Tickets in epic subdirectories are visually distinguishable from ungrouped tickets
