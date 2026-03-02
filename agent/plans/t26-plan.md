# T26 Plan: Add epic support to ticket system

## Context

The ticket list has grown to ~50 files in a flat directory. Epics (subdirectories) provide physical grouping without changing the flat-file ticket format. Design decisions are already locked in from the T26 design discussion.

## Approach

### 1. Update `ticket-format.md` with epic directory convention

Add a new section documenting:
- Epics are subdirectories under `agent/tickets/` (e.g., `agent/tickets/board/`)
- Directory name IS the epic identity — no frontmatter field
- Optional `EPIC.md` per directory with title and description
- Ungrouped tickets stay at root
- Glob pattern for all tickets: `agent/tickets/**/t*.md`
- Shared context files (like `ci-background.md`) can live in epic directories too

### 2. Update `roadmap/SKILL.md` with epic awareness

Extend all four workflows:
- **Create**: Ask which epic (or root) to place the ticket in. Write to `agent/tickets/{epic}/t{N}-{slug}.md` or root.
- **Import**: Allow specifying a target epic for the batch. Default to root.
- **Query**: Add epic filter. Show epic column in results. Glob pattern becomes `agent/tickets/**/t*.md`.
- **Reorganize**: Add "move to epic" operation — physically `mv` a ticket file between directories.

Update the glob pattern at the top of the skill from `agent/tickets/t*.md` to `agent/tickets/**/t*.md`.

### 3. Update `workon/SKILL.md` with recursive glob

Change the glob in step 1 from `agent/tickets/t*.md` to `agent/tickets/**/t*.md`.

### 4. Update board's `tickets.ts` to scan subdirectories

`loadTickets(directory)` currently uses `readdirSync` on a single directory. Change to recursively discover ticket files in subdirectories.

`updateTicketStatus(ticketId, newStatus, directory)` has the same flat-scan pattern — update it too.

### 5. Create epic directories and move tickets

Per the ticket's proposed groupings:
- `agent/tickets/ci/` — T1, T2, T3, T4, T7, T8
- `agent/tickets/zed/` — T10, T11, T12, T13
- `agent/tickets/board/` — T20, T22, T23, T24, T25, T50
- `agent/tickets/specs/` — T18, T21, T30, T31, T32
- `agent/tickets/skills-audit/` — T27-T49 (except T46 which stays at root)

Move `ci-background.md` into `agent/tickets/ci/` since it's shared context for CI tickets.

Standalone tickets stay at root: T5, T6, T9, T14, T16, T17, T26, T46.

### 6. Create optional EPIC.md files

Add a brief `EPIC.md` in each epic directory with title and one-line description.

## Key files

**Modify:**
- `.claude/skills/shared/ticket-format.md` — add epic directory convention section
- `.claude/skills/roadmap/SKILL.md` — epic-aware workflows, recursive glob
- `.claude/skills/workon/SKILL.md` — recursive glob pattern
- `apps/sveltekit/board/src/lib/tickets.ts` — recursive `loadTickets` and `updateTicketStatus`
- `apps/sveltekit/board/src/lib/tickets.test.ts` — add tests for subdirectory scanning

**Create:**
- `agent/tickets/ci/EPIC.md`
- `agent/tickets/zed/EPIC.md`
- `agent/tickets/board/EPIC.md`
- `agent/tickets/specs/EPIC.md`
- `agent/tickets/skills-audit/EPIC.md`

**Move:** ~40 ticket files into their epic directories

## Verification

- `pnpm test` in `apps/sveltekit/board/` — existing tests still pass, new subdirectory tests pass
- `pnpm check` and `pnpm lint` — no type or lint errors
- All tickets still discoverable: glob `agent/tickets/**/t*.md` returns same count as before
- Skill prose review: ticket-format.md, roadmap SKILL.md, workon SKILL.md all reference recursive patterns
