---
id: T45
title: Add TypeScript/Vitest testing conventions to shared docs
status: ready
depends_on: []
---

# T45: Add TypeScript/Vitest testing conventions to shared docs

## Goal

Document TypeScript testing conventions for the SvelteKit app, either as a section in testing.md or a separate testing-web.md.

## Context

testing.md only covers Python/pytest. The project has a SvelteKit app using Vitest and @testing-library/svelte, with brief conventions in CLAUDE.md Web Conventions. As the web frontend grows, the workon skill's TDD cycle needs testing conventions it can reference for TypeScript tickets, just like it references testing.md for Python tickets.

## Key files

- `.claude/skills/shared/testing.md` — current Python-only testing conventions
- CLAUDE.md — Web Conventions section (brief Vitest mention)
- `apps/sveltekit/board/` — existing test files to derive conventions from

## Done when

- TypeScript/Vitest testing conventions are documented in shared docs
- Covers: file placement, naming, framework (Vitest + testing-library), component testing patterns
- workon skill can reference the conventions for web tickets
