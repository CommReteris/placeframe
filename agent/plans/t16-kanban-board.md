# T16: Kanban board and frontmatter system

## Goal

Add YAML frontmatter to all ticket files as the machine-readable source of truth, build a `uv run board` web UI for visual kanban interaction, and restructure skills around two unambiguous verbs: `/workon` (implement a ticket) and `/roadmap` (manage the system).

## Context

The roadmap currently uses plain markdown with status tracked manually in `roadmap.md`. This doesn't scale to 50-500 tickets. YAML frontmatter on each ticket file gives programmatic access to status and dependencies. A web-based kanban board (Litestar + htmx + Sortable.js) provides drag-and-drop status management. All dependencies are independently-maintained FOSS — no VC-backed projects.

Jinja2 and litestar-htmx are already installed in the workspace. The only new Python dependencies are `python-frontmatter`, `mistune`, and `uvicorn`.

### Skill surface redesign

The old `/ticket` skill was ambiguous — the name suggests ticket management, but the skill only handles "work on a ticket." The old `/intake` skill (T15, never built) was too narrow — only bulk import. The new surface:

- **`/workon`** — Pick up a ticket and work through its lifecycle (design → plan → implement → verify → done). Replaces `/ticket`.
- **`/roadmap`** — Manage the roadmap system: create tickets, bulk import, query status, reorganize. Replaces the planned `/intake` (T15), which is now superseded.

T15 is superseded by this ticket.

## Key files

- `agent/plans/t*.md` — all ticket files (add frontmatter)
- `scripts/pyproject.toml` — add deps + entry point
- `scripts/src/scripts/tickets.py` — new shared ticket module
- `scripts/src/scripts/board.py` — new web UI + CLI
- `scripts/src/scripts/board_templates/` — Jinja2 templates (board.html, _column.html, _card.html, _detail.html)
- `scripts/src/scripts/board_static/` — vendored htmx.min.js, Sortable.min.js, board.js
- `.claude/skills/shared/ticket-format.md` — new shared format reference
- `.claude/skills/workon/SKILL.md` — new (replaces `.claude/skills/ticket/SKILL.md`)
- `.claude/skills/roadmap/SKILL.md` — new (replaces planned `/intake`)

## Approach

### 1. Add frontmatter to all ticket files

Add YAML frontmatter block to the top of each `agent/plans/t*.md` file:

```yaml
---
id: T3
title: Snapshot tests for build.py argument assembly
status: plan-needed
depends_on: [T2]
---
```

Schema: `id` (string), `title` (string), `status` (one of: blocked, design-needed, plan-needed, ready, done), `depends_on` (list of ticket ID strings). Status and dependency values extracted from current `roadmap.md`. `ci-background.md` is shared context, not a ticket — no frontmatter.

### 2. Add dependencies to scripts package

In `scripts/pyproject.toml`, add: `python-frontmatter>=1.1.0`, `mistune>=3.1.0`, `uvicorn>=0.35.0`, `litestar>=2.19.0`, `jinja2>=3.1.0`. Add `"uvicorn"` to DEP002 deptry exceptions. Add entry point `board = "scripts.board:main"`. Then `uv sync --all-packages` and `uv run generate-lock-files`.

### 3. Create tickets module

New file `scripts/src/scripts/tickets.py`. Shared module independent of Litestar (reusable by future CLI tools). Contains:

- `PLANS_DIRECTORY` — resolved path to `agent/plans/`
- `STATUSES` — ordered list: blocked, design-needed, plan-needed, ready, done
- `Ticket` dataclass — id, title, status, depends_on, body (raw markdown), file_path
- `load_tickets(directory)` — glob `t*.md`, parse frontmatter via `frontmatter.load()`
- `tickets_by_status(tickets)` — group by status in column display order
- `update_ticket_status(ticket_id, new_status, directory)` — read file, update `status` field in frontmatter, write back with `frontmatter.dumps()`
- `generate_roadmap(tickets, output_path)` — write `roadmap.md` from ticket data, keeping a static header (intro, status definitions) and generating the ticket list section

### 4. Create board templates

New directory `scripts/src/scripts/board_templates/` with four files:

- `board.html` — full page shell with inline `<style>` block (flexbox columns, card styling, status colors: blocked=red, design-needed=orange, plan-needed=amber, ready=green, done=gray), header with search input, `#board-columns` div, `#detail-panel` aside
- `_column.html` — single status column with header + count, `.column-cards` div with `data-status` for Sortable.js
- `_card.html` — ticket card showing ID, title, dependency badges; `hx-get="/tickets/{id}"` + `hx-target="#detail-panel"` for click-to-detail
- `_detail.html` — side panel with ticket metadata and rendered markdown body (via `mistune.html()`)

### 5. Vendor static assets

New directory `scripts/src/scripts/board_static/` with:

- `htmx.min.js` — vendored from htmx.org (0-clause BSD)
- `Sortable.min.js` — vendored from SortableJS GitHub releases (MIT)
- `board.js` — ~30 lines: initialize Sortable.js on `.column-cards`, fire `htmx.ajax('PATCH', ...)` on drop, re-initialize after htmx swaps, client-side search filtering

### 6. Create board script

New file `scripts/src/scripts/board.py`. Typer CLI with `main()` function. CLI: `uv run board [--port 8080] [--host 127.0.0.1]`.

Litestar app created directly (not using `create_litestar_app()` from common — that adds auth/OpenAPI which aren't relevant). Three routes:

- `GET /` — render full kanban board
- `GET /tickets/{ticket_id}` — render ticket detail partial (htmx)
- `PATCH /tickets/{ticket_id}` — update status from drag-and-drop, return all columns

Plus static file router for `/static/`. Uses `HTMXPlugin` from `litestar_htmx`. Calls `generate_roadmap()` on startup. No caching — reading 500 frontmatter files takes ~100ms, fine for single-user dev tool.

### 7. Create shared ticket format reference

New file `.claude/skills/shared/ticket-format.md`. Documents: frontmatter schema, status values and meanings, status transitions, file naming convention (`t{N}-{slug}.md`), ticket body structure (Goal, Context, Approach, Done when), `depends_on` conventions.

### 8. Create /workon skill (replaces /ticket)

New file `.claude/skills/workon/SKILL.md`. Same workflow as current `/ticket` but:
- Reads ticket status from frontmatter (not roadmap.md prose)
- Updates status via frontmatter writes
- Regenerates `roadmap.md` after status changes
- References shared `ticket-format.md`
- Name clearly communicates "do the work"

Delete `.claude/skills/ticket/`.

### 9. Create /roadmap skill (replaces planned /intake)

New file `.claude/skills/roadmap/SKILL.md`. Handles multiple intents:

- **Create a ticket**: Assign next T-number, write frontmatter + detail file, add to roadmap. Plan content from current session gets inlined into the detail file (never reference ephemeral plan files).
- **Bulk import**: Extract items from user input, deduplicate against existing tickets, triage with user, create stubs with status `design-needed`.
- **Query**: Read ticket frontmatter, present filtered results (by status, dependencies, etc.).
- **Reorganize**: Update dependencies, change statuses, merge/split tickets.

After any modification, regenerate `roadmap.md` from frontmatter.

### 10. Mark T15 superseded

Update T15 status to `done` (superseded by T16's `/roadmap` skill). Note in the file that it was absorbed into T16.

## Done when

**Verifiable now:**
- `uv sync --all-packages` succeeds
- `uv run generate-lock-files` succeeds
- `uv run deptry-check` passes
- `uv run ruff check .` passes
- `uv run ruff format --check .` passes
- `uv run basedpyright` passes for new files
- `uv run board` starts server on port 8080
- All ticket files have valid YAML frontmatter
- `roadmap.md` is generated from frontmatter and matches ticket states
- `/workon` skill exists and references shared ticket-format.md
- `/roadmap` skill exists with create, import, query, reorganize workflows
- `/ticket` skill is removed
- T15 marked as superseded

**Requires browser (manual verification):**
- Kanban board renders 5 columns with cards at `http://127.0.0.1:8080`
- Clicking a card shows detail panel with rendered markdown
- Dragging a card between columns updates frontmatter on disk
- Search input filters cards by text
