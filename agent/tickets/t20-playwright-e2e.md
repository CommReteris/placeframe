---
id: T20
title: Playwright E2E testing for board app
status: plan-needed
depends_on: [T18]
---

# T20: Playwright E2E testing for board app

## Goal

Add Playwright end-to-end testing to the SvelteKit board app, covering interaction-level behavior that jsdom-based unit tests fundamentally cannot catch — particularly drag-and-drop between columns.

## Context

During T16 implementation, two bugs shipped that passed all existing tests: tickets not rendering in the UI (a data-to-component wiring issue) and drag-and-drop causing tickets to vanish (an interaction-level bug in the finalize handler). The first class could be caught by component tests in jsdom. The second cannot — jsdom has no layout engine, no real pointer events, and `svelte-dnd-action` relies on actual DOM coordinates.

Playwright runs a real browser and can click, drag, drop, and assert on real layout. The setup cost (browser binaries, CI configuration) is a one-time investment. The app is small today but we're planning for six months from now — if Playwright catches bugs that are structurally invisible to the rest of the test stack, the investment is correct regardless of current app size.

This is the first ticket completed fully under the new spec-aware workflow from T18. The board's SPEC.md (from T19) should be updated (with user approval) to reflect the new testing infrastructure.

## Key files

- `apps/sveltekit/board/playwright.config.ts` — Playwright configuration
- `apps/sveltekit/board/e2e/` — E2E test files
- `apps/sveltekit/board/package.json` — new scripts and devDependencies
- `apps/sveltekit/board/SPEC.md` — updated to reflect E2E testing setup

## Approach

### 1. Install Playwright

In `apps/sveltekit/board/`: `pnpm add -D @playwright/test` and `pnpm exec playwright install chromium`.

### 2. Add `BOARD_PLANS_DIR` env var override to `plans-dir.ts`

Change the hardcoded path to: `process.env["BOARD_PLANS_DIR"] ?? path.resolve(process.cwd(), "../../../agent/tickets")`. This lets tests point at a fixture directory without touching real ticket files.

### 3. Add `data-testid` attributes to components

- **Column.svelte**: `data-testid="column-{status}"` on the column root div
- **Card.svelte**: `data-testid="card-{ticket.id}"` on the button element

### 4. Create `playwright.config.ts`

Chromium-only (headless), `webServer` config to auto-start `pnpm dev` with `BOARD_PLANS_DIR` pointing to fixture dir, test dir `e2e/`, html reporter.

### 5. Test fixture system (`e2e/fixtures.ts`)

- 6 fixture tickets covering all 5 statuses (two in `ready` for multi-card testing), one with dependencies
- `writeFixtureTickets()` writes markdown files to a temp dir
- `resetFixtureTickets()` restores original state after DnD mutation
- `dragCardToColumn()` helper: pointer event sequence (mousedown → mousemove with steps → mouseup → wait for network)

### 6. Global setup/teardown

- `e2e/global-setup.ts`: Creates fixture dir, writes fixture files
- `e2e/global-teardown.ts`: Removes fixture dir

### 7. Test files (3 files, ~18 tests)

**`e2e/board.test.ts`** — Board rendering (5 tests): column rendering, labels/counts, card content, dependency badges, numeric sort order.

**`e2e/drag-and-drop.test.ts`** — DnD with persistence (3 tests): ticket moves to new column, status persists after reload, column counts update.

**`e2e/detail-panel.test.ts`** — Detail panel and search (10 tests): panel open/close (3 methods), content display, markdown rendering, resize, search by title/ID, empty search results.

### 8. Package.json and .gitignore

Add `"test:e2e": "playwright test"` script. Add `test-results/`, `playwright-report/`, `/blob-report/` to gitignore.

### 9. CLAUDE.md update

Add browser install note to environment notes.

### Key technical details

**DnD helper**: `svelte-dnd-action` activates on pointer events with ~3px movement threshold. The helper gets bounding boxes, does mousedown on source, mousemove in 10 steps to target, mouseup, then waits for the PATCH request to complete.

**Resize helper**: Get the `cursor-col-resize` element, mousedown (triggers `pointerdown` + `setPointerCapture`), mousemove horizontally, mouseup, assert width via computed style.

**Test data reset**: `beforeEach` rewrites fixture files. SvelteKit dev server reads files on each SSR request so always sees current state.

## Done when

### Verifiable now
- `@playwright/test` is installed as a devDependency
- `playwright.config.ts` exists with sensible defaults (Chromium at minimum)
- pnpm scripts exist for running E2E tests (`pnpm test:e2e` or similar)
- E2E tests cover: ticket rendering in columns, drag-and-drop between columns with persistence, detail panel open/close, detail panel resize, search filtering, markdown rendering in detail panel
- The drag-and-drop test specifically verifies the ticket appears in the new column after drop (the bug that shipped in T16)
- All E2E tests pass
- CLAUDE.md environment notes updated if browser install needs documentation

### Requires manual verification
- Tests run reliably (no flakiness in DnD tests)
- Board SPEC.md updated with user approval to reflect E2E testing setup
