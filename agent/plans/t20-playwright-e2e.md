---
id: T20
title: Playwright E2E testing for board app
status: plan-needed
depends_on: [T18, T19]
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

To be written during plan mode.

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
