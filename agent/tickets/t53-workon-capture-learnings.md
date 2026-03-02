---
id: T53
title: Add "capture learnings" step to workon skill
status: in-review
depends_on: []
---

# T53: Add "capture learnings" step to workon skill

## Goal

Add a step to the workon skill that reviews implementation failures (from the ticket log) and proposes documentation updates to help future sessions avoid the same pitfalls. Currently this knowledge only surfaces if the user manually calls `/debrief` before clearing context.

## Context

During T50 implementation, several hard-won insights emerged (Svelte 5 reactivity pitfalls, E2E hydration timing, SvelteKit lint rule workarounds). These were captured in the ticket's `## Log` section but would have been lost to future sessions if `/debrief` hadn't been called. The debrief skill scans the full conversation — what's needed is a focused, ticket-scoped step that runs automatically as part of the workon lifecycle.

The ticket log records *what* went wrong. The new step elevates that to *where the knowledge should live permanently* — CLAUDE.md conventions, testing docs, skill tweaks, or shared guidance files.

## Key files

- `.claude/skills/workon/SKILL.md` — add new step 6 (renumber existing 6→7, 7→8, 8→9)

## Approach

Add a new step 6 "Capture learnings" between verify (step 5) and spec maintenance (current step 6). The step:

1. Re-reads the ticket's `## Log` section
2. For each failure/pivot: asks whether it's ticket-specific or generalizable
3. For generalizable items: proposes where the knowledge should live (CLAUDE.md, testing docs, skill files, shared guidance)
4. Presents proposals to the user — they pick which to capture
5. Writes approved items to the appropriate files

This is prose-only — no code changes, just a skill file edit.

## Done when

- Workon SKILL.md has a new step between verify and spec maintenance
- The step is scoped to the ticket's log (not a full conversation scan like debrief)
- The step proposes destinations for each learning (CLAUDE.md, testing docs, etc.)
- The step requires user approval before writing anything
- Existing step numbering is updated consistently

## Log

Clean implementation, no issues.
