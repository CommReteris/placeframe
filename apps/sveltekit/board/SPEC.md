# Placeframe Board

## What it does

A SvelteKit kanban board for managing Placeframe roadmap tickets. Reads ticket markdown files (with YAML frontmatter) from `agent/tickets/`, displays them across five status columns, and supports drag-and-drop status changes, a resizable detail drawer, and client-side search.

## Behaviors

### Board layout

- When the page loads, renders five columns in order: Blocked, Design needed, Plan needed, Ready, Done.
- Each column header shows a colored status dot, the status label, and a ticket count.
- Tickets are sorted numerically by T-number within each column.

### Cards

- Each card displays the ticket ID, title, and dependency count (if any).
- When a card is clicked, the detail panel opens for that ticket.
- When a card is dragged to a different column, a PATCH request updates the ticket's status in the frontmatter on disk, then all board data is revalidated.

### Detail panel

- Opens as a right-side drawer overlay with a semi-transparent backdrop.
- Displays ticket ID, title, status, dependencies, and the ticket body rendered as HTML via `marked`.
- Closes on backdrop click, Escape key, or the close button.
- The left edge is a drag handle for resizing (minimum 320px, default 672px).
- Width persists within a session but resets on page reload. Gap: localStorage persistence would be better (T24).

### Search

- Filters cards client-side by title and ticket ID (case-insensitive).
- Gap: does not filter by status or dependency — both would be useful (T23).

### Ticket data

- Reads `.md` files matching `t\d+.*\.md` from the tickets directory.
- Parses YAML frontmatter for id, title, status, and depends_on; everything after frontmatter is the body.
- Files without valid frontmatter are silently skipped.

### API

- `PATCH /api/tickets/[id]` — accepts `{ status }`, validates against the five allowed statuses, writes updated frontmatter to disk, returns the updated ticket. Returns 400 for invalid status, 404 if ticket not found.

### Gaps

- No live refresh: if a ticket file changes on disk while the board is open, the board does not update until a page reload or a drag-drop operation (T22).

## Design decisions

- **Dark-only theme with oklch tokens** — all colors defined as CSS custom properties in `@theme`, using oklch for perceptual uniformity. Each status has a distinct hue.
- **SSR for initial load** — `+page.server.ts` loads all tickets server-side; subsequent interactions (drag-drop, search) are client-side.
- **svelte-dnd-action for drag-and-drop** — Svelte-native, independently maintained FOSS library. Provides `onconsider`/`onfinalize` events for responsive drag feedback.
- **`@html` for markdown rendering** — uses `marked` to render ticket bodies. Trusted content: only renders local ticket files from `agent/tickets/`, never user-submitted content.
- **TypeScript ticket module mirrors Python `tickets.py`** — same YAML frontmatter format, same file discovery pattern (`t\d+.*\.md`), same sort order. The board reads the same files the `/roadmap` and `/workon` skills write.
- **Tickets directory resolved via `process.cwd()`** — currently `path.resolve(process.cwd(), "../../../agent/tickets")`. This is fragile and couples the app to being run from a specific working directory. Should be improved to use a SvelteKit `$env` variable or similar configuration (T25).
- **Pointer capture for resize handle** — ensures smooth dragging even when the cursor moves off the handle during resize.

## Key files

- `src/lib/tickets.ts` — ticket types, YAML frontmatter parsing, file I/O, status grouping
- `src/lib/tickets.test.ts` — unit tests for all ticket module functions
- `src/lib/server/tickets-dir.ts` — tickets directory path resolution
- `src/lib/components/Board.svelte` — column grid, drag-and-drop state management
- `src/lib/components/Column.svelte` — single status column with dndzone
- `src/lib/components/Card.svelte` — ticket card (ID, title, dep count)
- `src/lib/components/DetailPanel.svelte` — resizable right-side drawer with rendered markdown
- `src/lib/components/SearchBar.svelte` — search input with two-way binding
- `src/routes/+page.server.ts` — SSR data loading (all tickets grouped by status)
- `src/routes/+page.svelte` — page layout, search state, detail panel toggle
- `src/routes/api/tickets/[id]/+server.ts` — PATCH endpoint for status changes
- `src/app.css` — dark theme tokens and prose overrides
