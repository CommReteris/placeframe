---
id: T50
title: Board UI epic grouping
status: design-needed
depends_on: []
---

# T50: Board UI epic grouping

## Goal

Add epic awareness to the board app — both in the data model and the UI — so tickets are visually grouped by their epic subdirectory. Design the epic-aware data layer as a foundation for future views (list, dependency graph, roadmap) beyond the current kanban.

## Context

Epic subdirectories already exist under `agent/tickets/` (`board/`, `ci/`, `zed/`, `specs/`, `skills-audit/`). The data layer (`loadTickets()`) already recursively scans them and preserves `filePath` on each ticket. What's missing is:

1. **Data model** — the `Ticket` interface has no `epic` field. The epic can be derived from `filePath` (parent directory name, or `null` for root-level tickets), but nothing does this yet.
2. **UI** — the board has no awareness of epics. No badges, no filtering, no grouping.

This is the first step toward the board becoming a multi-view project tool rather than a flat kanban. The epic-aware data layer should be designed so that a future list view, dependency graph, or epic roadmap view can consume the same grouped data without rearchitecting.

### Current ticket distribution by epic

- `board/` — 8 tickets (T20, T22–T25, T50, T51, T52)
- `ci/` — 8 tickets (T1–T8)
- `zed/` — 4 tickets (T10–T13)
- `specs/` — 1 ticket
- `skills-audit/` — 1 ticket
- root (ungrouped) — ~10 tickets

### What this is NOT

- Not adding new frontmatter fields — epic identity comes from directory structure, not metadata.
- Not adding EPIC.md files or epic-level configuration — keep it simple.
- Not building other views yet — just making the kanban epic-aware and ensuring the data layer supports future views.

## Key files

- `apps/sveltekit/board/src/lib/tickets.ts` — add `epic` field to Ticket interface, derive from filePath
- `apps/sveltekit/board/src/lib/components/Card.svelte` — show epic badge
- `apps/sveltekit/board/src/lib/components/Board.svelte` — potential layout changes for grouping
- `apps/sveltekit/board/src/routes/+page.svelte` — epic filter control

## Approach

TBD — needs design discussion. Open questions:

1. **Filtering vs. grouping vs. both?** Filter dropdown (show one epic at a time) is simple. Grouping (swimlanes or colored sections within columns) is richer but more complex. Could start with filtering and add grouping later.
2. **Visual treatment** — small colored chip on each card? Epic-colored left border? Subtle background tint per epic? Needs to work with the existing dark theme.
3. **URL state** — should the active epic filter be in the URL (shareable, bookmarkable) or just client state?
4. **"All" vs. default** — when no filter is active, show all tickets (current behavior). The filter adds specificity, doesn't remove it.

## Done when

- Ticket interface has an `epic` field (string | null, derived from directory path)
- Board cards show which epic they belong to (badge, chip, or similar)
- User can filter the board to show only tickets from a specific epic
- Ungrouped (root-level) tickets display cleanly without an epic label
- Existing unit tests and E2E tests still pass
- New E2E test verifies epic filtering works
