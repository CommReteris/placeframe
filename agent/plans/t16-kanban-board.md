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

Technology stack (decided during planning): SvelteKit 2.x (Svelte 5) with runes (full-stack), TypeScript with maximum strictness + ts-reset, Node.js runtime, pnpm package manager, Tailwind CSS v4, svelte-dnd-action for drag-and-drop, Vitest + @testing-library/svelte for testing, ESLint flat config + eslint-plugin-svelte v3. All dependencies are independently-maintained FOSS — no VC-backed projects.

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

### 1. Install pnpm and scaffold SvelteKit app

```bash
npm install -g pnpm
mkdir -p apps/sveltekit
cd apps/sveltekit
pnpm dlx sv create board --types ts
cd board
pnpm dlx sv add tailwindcss
pnpm dlx sv add eslint
pnpm dlx sv add vitest
pnpm add svelte-dnd-action yaml marked
pnpm add -D @total-typescript/ts-reset @testing-library/svelte @testing-library/jest-dom @types/marked
```

### 2. Configure TypeScript (maximum strictness)

Edit `tsconfig.json` — add `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noPropertyAccessFromIndexSignature`, `noImplicitOverride`, `noImplicitReturns`, `noFallthroughCasesInSwitch`, `allowUnreachableCode: false`, `allowUnusedLabels: false` on top of SvelteKit's generated base (which already includes `strict: true`). Create `src/reset.d.ts` importing `@total-typescript/ts-reset`.

### 3. Configure Tailwind v4 (dark theme)

`@tailwindcss/vite` must come before `sveltekit()` in `vite.config.ts`. Define dark-only theme with CSS custom properties in `src/app.css` using `@theme` — surface colors, text colors, border colors, and per-status colors (blocked, design-needed, plan-needed, ready, done) using oklch.

### 4. TypeScript ticket module (`src/lib/tickets.ts`)

Port the Python `tickets.py` logic to TypeScript. Types: `Ticket` (id, title, status, dependsOn, body, filePath), `Status` union type. Functions: `parseFrontmatter`, `dumpFrontmatter`, `loadTickets`, `loadTicket`, `updateTicketStatus`, `ticketsByStatus`. Uses `yaml` npm package for YAML parsing and Node.js `fs` for file I/O. Path resolution via `$env/static/private` or `path.resolve(import.meta.dirname, '../../../../agent/plans/')`.

### 5. Server routes

- **`+page.server.ts`** — load all tickets grouped by status for SSR
- **`api/tickets/[id]/+server.ts`** — PATCH to update ticket status (called by drag-and-drop)

### 6. Board UI components

File structure under `src/lib/components/`:
- `Board.svelte` — grid of columns, manages drag-and-drop state
- `Column.svelte` — status column with dndzone (svelte-dnd-action)
- `Card.svelte` — ticket card (id, title, dependency count)
- `DetailPanel.svelte` — sidebar with ticket metadata and rendered markdown body (using `marked`)
- `SearchBar.svelte` — filter input

All components use Svelte 5 runes (`$state`, `$derived`, `$props`). Board uses `onconsider`/`onfinalize` events from svelte-dnd-action. On finalize (drop), PATCH the moved ticket's new status.

### 7. Search/filter

Client-side filtering with `$state` search term and `$derived` filtered tickets. Filters by title and ticket id.

### 8. Create /roadmap skill

New file `.claude/skills/roadmap/SKILL.md`. Four workflows:
- **Create**: assign next T-number, write frontmatter + detail file, regenerate roadmap
- **Bulk import**: extract items from user input, deduplicate, triage, create stubs
- **Query**: read frontmatter, filter by status/dependencies, present results
- **Reorganize**: update dependencies, change statuses, merge/split tickets

### 9. Add web dev conventions to CLAUDE.md

TypeScript (strict, no `any`, prefer `satisfies` over `as`), Svelte 5 (runes only, no Svelte 4 syntax), component guidelines, naming conventions, Tailwind styling rules, file extension conventions.

### 10. Clean up old board artifacts

Delete the abandoned Jinja2/htmx files: `scripts/src/scripts/board_templates/`, `scripts/src/scripts/board_static/`, and `scripts/src/scripts/board.py` (if created). Remove board-specific dependencies from `scripts/pyproject.toml` (mistune, uvicorn — keep only what tickets.py needs).

## Done when

**Verifiable now:**
- `pnpm install` succeeds in `apps/sveltekit/board/`
- `pnpm check` (svelte-check TypeScript) passes with zero errors
- `pnpm lint` (ESLint + svelte plugin) passes
- `pnpm build` produces a production build
- `pnpm test` (Vitest) passes
- `/roadmap` skill exists with create, import, query, reorganize workflows
- Old board artifacts (board_templates/, board_static/) are deleted

**Requires browser (manual verification):**
- Kanban board renders 5 columns with cards at `http://localhost:5173`
- Clicking a card shows detail panel with rendered markdown
- Dragging a card between columns updates frontmatter on disk
- Search input filters cards by title/id
