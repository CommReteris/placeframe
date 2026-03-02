# TypeScript/Vitest Testing Conventions

For the SvelteKit board app (`apps/sveltekit/board/`). Run tests with `pnpm --dir apps/sveltekit/board test`.

## Framework

Vitest + `@testing-library/svelte`. Config in `vitest.config.ts` (jsdom environment, setup file at `src/test-setup.ts`).

## File placement

Tests live alongside the code they test: `src/lib/tickets.test.ts` tests `src/lib/tickets.ts`. Pattern: `*.test.ts` in the same directory as the source file.

## Naming

- **Test blocks**: `describe("<Unit>", () => { ... })` groups related tests for a function or component.
- **Test cases**: `it("should <expected> when <condition>", () => { ... })` — describes behavior, not implementation.
- **Factory functions**: `makeFoo()` with sensible defaults and overrides, same as Python conventions.

## Pattern

Arrange-Act-Assert, same as Python. One logical assertion per test.

```typescript
it("should parse status when valid frontmatter", () => {
	const text = "---\nid: T1\nstatus: ready\n---\nBody";

	const result = parseFrontmatter(text);

	expect(result.metadata["status"]).toBe("ready");
});
```

## Mocking

Same boundaries as Python — mock external APIs, filesystem, time. Use real temp directories (`fs.mkdtempSync`) for filesystem tests, cleaned up in `afterEach`.

For Svelte components, use `@testing-library/svelte` `render()` and query the DOM. Prefer `getByRole`, `getByText` over `getByTestId`.

## Fixtures and setup

- Factory functions over complex setup. Same pattern as Python: `makeTicketFile()` with defaults.
- `beforeEach`/`afterEach` for temp directory creation and cleanup.
- Global setup in `src/test-setup.ts` (DOM matchers, etc.).

## E2E (Playwright)

Playwright E2E tests live in `e2e/`. Config in `playwright.config.ts` (Chromium-only, single worker, dev server via `pnpm dev`).

- **Hydration timing**: `page.goto("/")` returns before Svelte 5 hydration completes. Tests that interact with components (click, selectOption, type) must call `await page.waitForLoadState("networkidle")` after `goto()` — otherwise event handlers aren't attached yet. Tests that only read the DOM (check visibility, text content) don't need this.
- **Fixture isolation**: `beforeEach` calls `writeFixtureTickets()` to reset the fixture directory. Fixtures support `subdirectory` for epic-aware tests.
- **Stable selectors**: Use `data-testid` attributes, not CSS classes or DOM structure. Pattern: `data-testid="card-{ticket.id}"`, `data-testid="column-{status}"`.
- **DnD testing**: Playwright's `dragTo()` doesn't reliably carry `dataTransfer` data for native HTML5 DnD. Use synthetic `DragEvent` dispatch via `page.evaluate()`.

## What not to test

Same as Python: auto-generated code, third-party internals, pure config, trivial property access.
