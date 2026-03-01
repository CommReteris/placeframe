---
id: T16
title: Kanban board web UI
status: ready
depends_on: [T17]
---

# T16: Kanban board web UI

## Goal

Build a SvelteKit kanban board at `apps/sveltekit/board/` for visual ticket management — drag-and-drop status changes, detail panels, search/filter. Reads and writes YAML frontmatter on ticket files (infrastructure provided by T17).

## Context

T17 provides the machine-readable ticket infrastructure: YAML frontmatter on all ticket files, `tickets.py` for parsing/updating, and the `/workon` skill. This ticket builds the visual layer on top — a web-based kanban board for quick status overview and drag-and-drop management.

Technology stack (decided during planning): SvelteKit 5 with runes (full-stack), TypeScript with maximum strictness + ts-reset, Node.js runtime, Yarn Berry package manager, Tailwind CSS, svelte-dnd-action for drag-and-drop. All dependencies are independently-maintained FOSS — no VC-backed projects.

The `/roadmap` skill (create tickets, bulk import, query, reorganize) is also part of this ticket — it provides the CLI counterpart to the board's visual management.

Depends on T17.

## Key files

- `apps/sveltekit/board/` — SvelteKit application (new)
- `apps/sveltekit/board/package.json` — dependencies and scripts
- `apps/sveltekit/board/src/routes/` — SvelteKit routes (board, ticket detail, status update API)
- `apps/sveltekit/board/src/lib/` — shared components and ticket parsing logic
- `scripts/src/scripts/tickets.py` — existing ticket module (T17, read by board's server routes)
- `.claude/skills/roadmap/SKILL.md` — new (replaces planned `/intake`)

## Approach

*Note: This plan will be revised in detail when T17 is complete and the SvelteKit architecture is finalized. The decisions below capture the technology choices made during planning. The old Jinja2/htmx/Litestar approach (board_templates/, board_static/, board.py) is abandoned in favor of SvelteKit.*

### 1. Scaffold SvelteKit app

Create `apps/sveltekit/board/` using SvelteKit 5 with runes. Initialize with Yarn Berry, TypeScript (maximum strictness + ts-reset), Tailwind CSS, ESLint + svelte plugin. Add svelte-dnd-action for kanban drag-and-drop.

### 2. Implement board UI

SvelteKit routes:
- `GET /` — render full kanban board with 5 status columns
- `GET /tickets/[id]` — ticket detail view with rendered markdown
- `PATCH /tickets/[id]` — update status from drag-and-drop (server route reads/writes YAML frontmatter)

Components: Board (grid of columns), Column (status group with cards), Card (ticket summary), DetailPanel (full ticket view with rendered markdown body).

### 3. Server-side ticket integration

SvelteKit server routes read ticket files from `agent/plans/` using the same frontmatter schema defined in T17's `ticket-format.md`. Implement TypeScript equivalents of `tickets.py` functions (parse frontmatter, load tickets, update status, group by status).

### 4. Create /roadmap skill

New file `.claude/skills/roadmap/SKILL.md`. Handles:
- **Create**: Assign next T-number, write frontmatter + detail file, regenerate roadmap
- **Bulk import**: Extract items, deduplicate, triage with user, create stubs
- **Query**: Filter by status, dependencies
- **Reorganize**: Update dependencies, change statuses, merge/split

### 5. Clean up old board artifacts

Delete the abandoned Jinja2/htmx files: `scripts/src/scripts/board_templates/`, `scripts/src/scripts/board_static/`, and `scripts/src/scripts/board.py` (if created). Remove board-specific dependencies from `scripts/pyproject.toml` (mistune, uvicorn — keep only what tickets.py needs).

## Done when

**Verifiable now:**
- `yarn install` succeeds in `apps/sveltekit/board/`
- `yarn check` (TypeScript) passes with zero errors
- `yarn lint` (ESLint + svelte plugin) passes
- `yarn build` produces a production build
- `/roadmap` skill exists with create, import, query, reorganize workflows
- Old board artifacts (board_templates/, board_static/) are deleted

**Requires browser (manual verification):**
- Kanban board renders 5 columns with cards
- Clicking a card shows detail panel with rendered markdown
- Dragging a card between columns updates frontmatter on disk
- Search input filters cards by text
