# Placeframe Board

## What it does

A SvelteKit kanban board for managing Placeframe roadmap tickets. Reads ticket markdown files (with YAML frontmatter) from `agent/tickets/`, displays them across six status columns, and supports drag-and-drop status changes, a resizable detail drawer, client-side search, and epic-based filtering and grouping.

## Behaviors

### Board layout

- When the page loads, renders six columns in order: Blocked, Design needed, Plan needed, Ready, In review, Done.
- Each column header shows a colored status dot, the status label, and a ticket count.
- Columns are separated by 24px (gap-6) of horizontal space.
- Within each column, tickets are grouped by epic. Named epics appear alphabetically, ungrouped (root-level) tickets appear last.
- Tickets are sorted numerically by T-number within each epic group.
- Cards within a column are separated by 10px (gap-2.5) of vertical space.
- The page title ("Placeframe Board") uses tight letter-spacing.

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
- Cards have 16px horizontal and 12px vertical padding.
- When a card is clicked, the detail panel opens for that ticket.
- When a card is dragged to a different column (native HTML5 drag-and-drop), a PATCH request updates the ticket's status in the frontmatter on disk, then all board data is revalidated. The ticket's epic does not change on drag — epic is derived from file path.

### Detail panel

- Opens as a right-side drawer overlay with a frosted backdrop (semi-transparent black with slight blur).
- Displays ticket ID, title, status, dependencies, and the ticket body rendered as HTML via `marked`.
- Closes on backdrop click, Escape key (via `<svelte:window>` so it works regardless of focus), or the close button.
- The left edge is a drag handle for resizing (minimum 320px, default 672px). The handle highlights with an accent color on hover and while dragging.
- Width persists within a session but resets on page reload. Gap: localStorage persistence would be better (T24).

### Search

- Filters cards client-side by title and ticket ID (case-insensitive).
- Gap: does not filter by status or dependency — both would be useful (T23).

### Interactions and transitions

- All interactive elements (cards, buttons, inputs, drop zones) transition color changes smoothly rather than snapping instantly.
- Cards use a 200ms transition for all visual properties (color, transform, shadow).
- When a card is hovered, it lifts slightly upward (2px) and its border and background brighten.
- When a card is clicked/pressed, it briefly scales down (98%) with a fast 75ms response, then returns to normal size.
- Epic section toggle buttons, the close button, and the resize handle all transition their background color smoothly on hover.
- The search input and epic filter dropdown brighten their border on hover (same treatment as focus).
- All interactive elements (cards, epic section buttons, drop zones, close button, inputs, select) show a visible focus ring when navigated via keyboard (focus-visible). The ring is a subtle white glow with an offset gap matching the element's background surface.
- The search input and epic filter dropdown show both a border brightening and a focus ring when focused via keyboard.

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

- **Dark-only theme with oklch tokens** — all colors defined as CSS custom properties in `@theme`, using oklch for perceptual uniformity. Each status has a distinct hue. Surface colors step by 0.05 lightness per elevation level. A dedicated accent color is defined for UI highlights (resize handle).
- **Epic colors in TypeScript, not CSS** — epic colors are defined in `epicColor()` with curated oklch values for known epics and a deterministic hash-to-hue fallback for unknown epics. Applied via inline styles rather than CSS custom properties, so new epics don't require CSS changes.
- **Epic identity from directory structure** — no frontmatter field needed. `deriveEpic()` computes the epic from the relative path. This keeps the data model simple and avoids requiring ticket authors to manually tag epics.
- **SvelteSet for collapse state** — `SvelteMap` `.get()` didn't reliably trigger Svelte 5 template re-renders. `SvelteSet<string>` with `.has()` / `.add()` / `.delete()` works correctly with Svelte 5's fine-grained reactivity.
- **`pushState` for epic filter URL** — uses SvelteKit's shallow routing (`pushState` from `$app/navigation`) to update the URL without triggering a server load. The `resolve()` wrapper from `$app/paths` satisfies the `no-navigation-without-resolve` lint rule.
- **SSR for initial load** — `+page.server.ts` loads all tickets server-side; subsequent interactions (drag-drop, search, epic filter) are client-side.
- **Native HTML5 drag-and-drop** — uses the browser's built-in drag-and-drop API (`draggable`, `ondragstart`, `ondragover`, `ondrop`) instead of a library. Cards stay in the source column during drag; after drop, `invalidateAll()` reloads data. Simpler, zero-dependency, and testable with Playwright.
- **Borders over shadows for depth** — follows Linear's dark UI pattern: surface-lightness steps and borders convey depth, not drop shadows. Shadows are reserved for truly floating elements (the detail panel drawer). This avoids the "invisible shadow on dark background" problem.
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
- `src/app.css` — dark theme tokens (surface, text, border, status, accent) and prose overrides
- `playwright.config.ts` — Playwright config (Chromium, single worker, fixture dir, dev server)
- `e2e/fixtures.ts` — test fixture definitions (root + subdirectory tickets) and temp directory helpers
- `e2e/board.test.ts` — board rendering E2E tests (columns, cards, epic group sorting)
- `e2e/drag-and-drop.test.ts` — DnD E2E tests (move, persist, counts)
- `e2e/detail-panel.test.ts` — detail panel and search E2E tests
- `e2e/epic-filter.test.ts` — epic chip, filter, URL state, and collapsible section E2E tests
