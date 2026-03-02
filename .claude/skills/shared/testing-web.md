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

## What not to test

Same as Python: auto-generated code, third-party internals, pure config, trivial property access.
