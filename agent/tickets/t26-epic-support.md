---
id: T26
title: Add epic support to ticket system
status: plan-needed
depends_on: []
---

# T26: Add epic support to ticket system

## Goal

Add an "epic" concept to the ticketing system so that large groups of related tickets (e.g., all action items from a skills audit) can be organized under a parent theme without losing the flat-file simplicity of the current system.

## Context

The skills audit (`agent/skills-audit.md`) produced ~23 discrete action items that each warrant their own ticket. The ticket list has grown from 25 to 49, and without grouping, `agent/tickets/` is an undifferentiated wall of files. Epics provide physical directory-based grouping for easier browsing and logical organization.

The current system uses flat markdown files with YAML frontmatter (`id`, `title`, `status`, `depends_on`). Any epic support should extend this rather than replace it.

### Design decisions (from T26 design discussion)

- **Epics are directories.** An epic is a subdirectory under `agent/tickets/` (e.g., `agent/tickets/board/`). The directory name IS the epic identity — no frontmatter `epic` field on individual tickets.
- **No frontmatter field.** The epic is derived from the file's path, not stored redundantly in YAML. One source of truth, zero drift.
- **Optional EPIC.md per directory.** Each epic directory may contain an `EPIC.md` with a title and description. Not required — a bare directory with just ticket files is a valid epic.
- **Ungrouped tickets stay at root.** Tickets without an epic remain in `agent/tickets/` directly. Epic membership is optional.
- **Extend /roadmap, no new skill.** Epic creation/query/reorganize are variants of existing roadmap workflows, not a separate skill.
- **Board UI is a separate ticket (T50).** Webapp epic support is blocked by this ticket.

## Key files

- `.claude/skills/shared/ticket-format.md` — frontmatter schema, add epic directory convention
- `.claude/skills/roadmap/SKILL.md` — extend create/import/query/reorganize with epic awareness
- `.claude/skills/workon/SKILL.md` — update ticket glob pattern
- `apps/sveltekit/board/src/lib/server/tickets.ts` — update glob to scan subdirectories

### Proposed epic groupings

Initial directories to create as proof-of-concept during implementation:

- **`ci/`** — T1, T2, T3, T4, T7, T8 (build/CI pipeline)
- **`zed/`** — T10, T11, T12, T13 (ZED camera hardware)
- **`board/`** — T20, T22, T23, T24, T25, T50 (kanban board features)
- **`specs/`** — T18, T21, T30, T31, T32 (spec system)
- **`skills-audit/`** — T27-T49 (skills audit action items)

Standalone tickets (T5, T6, T9, T14, T16, T17, T26, T46) stay at root.

## Approach

TBD — entering planning phase.

## Done when

**Verifiable now:**
- `ticket-format.md` documents the epic directory convention (subdirectories, optional EPIC.md, glob patterns)
- `/roadmap` skill prose supports creating epics, importing into epics, querying by epic, and moving tickets between epics
- `/workon` skill references the recursive glob pattern (`agent/tickets/**/t*.md`)
- At least one epic directory exists with tickets moved into it as proof-of-concept
- All existing tickets remain accessible (epic is optional, ungrouped tickets at root still work)
- Board's `tickets.ts` scans subdirectories (glob change only — UI grouping is T50)

**Requires manual verification:**
- Board still renders correctly with tickets in subdirectories
