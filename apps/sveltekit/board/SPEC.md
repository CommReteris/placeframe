# Placeframe Board

## What it does

A SvelteKit kanban board for managing Placeframe roadmap tickets. Reads ticket markdown files (with YAML frontmatter) from `agent/tickets/`, displays them across six status columns, and supports drag-and-drop status changes, a resizable detail drawer, client-side search, and epic-based filtering and grouping.

## Behaviors

### Board layout

- When the page loads, renders six columns in order: Blocked, Design needed, Plan needed, Ready, In review, Done.
- Each column header shows a colored status dot, the status label, and a ticket count.
- Within each column, tickets are grouped by epic. Named epics appear alphabetically, ungrouped (root-level) tickets appear last.
- Tickets are sorted numerically by T-number within each epic group.

### Epics

- Each ticket's epic is derived from its directory structure: tickets in `agent/tickets/ci/` have epic `"ci"`, tickets directly in `agent/tickets/` have no epic (`null`).
- Cards for epic tickets show a colored chip next to the ticket ID with the epic name. Root-level tickets show no chip.
- Each epic has a deterministic color: five known epics (board, ci, zed, specs, skills-audit) have curated oklch colors; unknown epics get a color computed from a string hash.
- Within each column, tickets are grouped under collapsible epic section headers showing a color dot, expand/collapse arrow (▼/▶), epic name, and ticket count.
- The ungrouped (null epic) section only shows a header when the column contains multiple epic groups. When all tickets in a column are ungrouped, no section header appears.
- Collapse state is client-side only — resets on page reload.

### Epic filtering

- A dropdown in the header filters the board by epic. Options: "All epics" (default) plus one entry per known epic.
- When an epic is selected, only tickets from that epic are shown across all columns.
- The active filter is stored in the URL as `?epic=<name>` via SvelteKit's `pushState`. Loading a URL with `?epic=ci` applies the filter on page load.
- Search and epic filter combine with AND logic.

### Cards

- Each card displays the ticket ID, an optional epic chip, title, and dependency count (if any).
- When a card is clicked, the detail panel opens for that ticket.
- When a card is dragged to a different column (native HTML5 drag-and-drop), a PATCH request updates the ticket's status in the frontmatter on disk, then all board data is revalidated. The ticket's epic does not change on drag — epic is derived from file path.

### Detail panel

- Opens as a right-side drawer overlay with a semi-transparent backdrop.
- Displays ticket ID, title, status, dependencies, and the ticket body rendered as HTML via `marked`.
- Closes on backdrop click, Escape key (via `<svelte:window>` so it works regardless of focus), or the close button.
- The left edge is a drag handle for resizing (minimum 320px, default 672px).
- Width persists within a session but resets on page reload. Gap: localStorage persistence would be better (T24).

### Search

- Filters cards client-side by title and ticket ID (case-insensitive).
- Gap: does not filter by status or dependency — both would be useful (T23).

### Ticket data

- Reads `.md` files matching `t\d+.*\.md` from the tickets directory, recursively scanning subdirectories.
- Parses YAML frontmatter for id, title, status, and depends_on; everything after frontmatter is the body.
- Derives `epic` from the directory structure: the first path segment relative to the tickets root, or `null` for root-level files.
- Files without valid frontmatter are silently skipped.

### API

- `PATCH /api/tickets/[id]` — accepts `{ status }`, validates against the six allowed statuses, writes updated frontmatter to disk, returns the updated ticket. Returns 400 for invalid status, 404 if ticket not found.

### Gaps

- No live refresh: if a ticket file changes on disk while the board is open, the board does not update until a page reload or a drag-drop operation (T22).

## Design decisions

- **Dark-only theme with oklch tokens** — all colors defined as CSS custom properties in `@theme`, using oklch for perceptual uniformity. Each status has a distinct hue. Epic colors also use oklch with curated hues for known epics and a deterministic hash-to-hue fallback for unknown epics.
- **Epic identity from directory structure** — no frontmatter field needed. `deriveEpic()` computes the epic from the relative path. This keeps the data model simple and avoids requiring ticket authors to manually tag epics.
- **`epicColor()` utility with fallback** — known epics get curated colors; unknown epics get a deterministic color from a string hash. Avoids maintaining a growing CSS file as new epics are added.
- **SvelteSet for collapse state** — `SvelteMap` `.get()` didn't reliably trigger Svelte 5 template re-renders. `SvelteSet<string>` with `.has()` / `.add()` / `.delete()` works correctly with Svelte 5's fine-grained reactivity.
- **`pushState` for epic filter URL** — uses SvelteKit's shallow routing (`pushState` from `$app/navigation`) to update the URL without triggering a server load. The `resolve()` wrapper from `$app/paths` satisfies the `no-navigation-without-resolve` lint rule.
- **SSR for initial load** — `+page.server.ts` loads all tickets server-side; subsequent interactions (drag-drop, search, epic filter) are client-side.
- **Native HTML5 drag-and-drop** — uses the browser's built-in drag-and-drop API (`draggable`, `ondragstart`, `ondragover`, `ondrop`) instead of a library. Cards stay in the source column during drag; after drop, `invalidateAll()` reloads data. Simpler, zero-dependency, and testable with Playwright.
- **`@html` for markdown rendering** — uses `marked` to render ticket bodies. Trusted content: only renders local ticket files from `agent/tickets/`, never user-submitted content.
- **TypeScript ticket module mirrors Python `tickets.py`** — same YAML frontmatter format, same file discovery pattern (`t\d+.*\.md`), same sort order. The board reads the same files the `/roadmap` and `/workon` skills write.
- **Tickets directory via env var with fallback** — `BOARD_TICKETS_DIR` env var if set, otherwise `path.resolve(process.cwd(), "../../../agent/tickets")`. The env var exists primarily for E2E test fixture isolation (pointing the dev server at a temp directory of synthetic tickets). Still fragile for production use; should be improved to use a SvelteKit `$env` variable (T25).
- **Pointer capture for resize handle** — ensures smooth dragging even when the cursor moves off the handle during resize.
- **`data-testid` attributes for E2E** — Column (`data-testid="column-{status}"`), Card (`data-testid="card-{ticket.id}"`), epic chip (`data-testid="epic-chip-{epic}"`), epic section (`data-testid="epic-section-{epic}"`), and epic filter (`data-testid="epic-filter"`) carry stable test selectors.
- **Playwright E2E with fixture isolation** — Chromium-only, single worker (shared fixture directory), global setup/teardown creates and cleans a temp directory of synthetic ticket files. `beforeEach` resets fixtures so DnD mutations don't leak between tests. DnD tests use synthetic `DragEvent` dispatch (Playwright's `dragTo()` doesn't reliably carry `dataTransfer` data for native HTML5 DnD). Interactive tests (filter, collapse) require `waitForLoadState("networkidle")` before user interaction to ensure Svelte 5 hydration is complete.

## Key files

- `src/lib/tickets.ts` — ticket types (including `epic` field, `EpicGroup`), YAML frontmatter parsing, file I/O, status grouping, `deriveEpic`, `collectEpics`, `groupByEpic`
- `src/lib/tickets.test.ts` — unit tests for all ticket module functions
- `src/lib/epic-colors.ts` — deterministic epic-to-oklch-color mapping
- `src/lib/server/tickets-dir.ts` — tickets directory path resolution (env var override)
- `src/lib/components/Board.svelte` — column grid, passes tickets and status-change callback to columns
- `src/lib/components/Column.svelte` — single status column with drag-and-drop, collapsible epic sections
- `src/lib/components/Card.svelte` — ticket card (ID, epic chip, title, dep count)
- `src/lib/components/DetailPanel.svelte` — resizable right-side drawer with rendered markdown
- `src/lib/components/SearchBar.svelte` — search input with two-way binding
- `src/routes/+page.server.ts` — SSR data loading (all tickets grouped by status, epic list)
- `src/routes/+page.svelte` — page layout, search state, epic filter state, detail panel toggle
- `src/routes/api/tickets/[id]/+server.ts` — PATCH endpoint for status changes
- `src/app.css` — dark theme tokens (surface, text, border, status, epic) and prose overrides
- `playwright.config.ts` — Playwright config (Chromium, single worker, fixture dir, dev server)
- `e2e/fixtures.ts` — test fixture definitions (root + subdirectory tickets) and temp directory helpers
- `e2e/board.test.ts` — board rendering E2E tests (columns, cards, epic group sorting)
- `e2e/drag-and-drop.test.ts` — DnD E2E tests (move, persist, counts)
- `e2e/detail-panel.test.ts` — detail panel and search E2E tests
- `e2e/epic-filter.test.ts` — epic chip, filter, URL state, and collapsible section E2E tests
