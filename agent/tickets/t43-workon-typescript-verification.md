---
id: T43
title: Add TypeScript verification to workon step 5
status: ready
depends_on: []
---

# T43: Add TypeScript verification to workon step 5

## Goal

Include TypeScript/SvelteKit verification tools in the workon verify step for web tickets.

## Context

workon step 5 only runs Python tools (ruff, basedpyright, pytest). Tickets involving the SvelteKit board or other TypeScript code would miss `pnpm check` (svelte-check) and `pnpm lint` (eslint). As the web frontend grows, this gap becomes more significant.

## Key files

- `.claude/skills/workon/SKILL.md` — step 5
- CLAUDE.md — Web Conventions section documents the TypeScript tooling

## Approach

Add to step 5: "For TypeScript/SvelteKit changes, also run `pnpm check` and `pnpm lint` from the relevant app directory (e.g., `apps/sveltekit/board/`). See CLAUDE.md Web Conventions."

## Done when

- Step 5 includes TypeScript verification commands
- Verification is conditional on the ticket touching web code (not run for pure Python tickets)
