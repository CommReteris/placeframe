# Ticket Format Reference

## Frontmatter schema

Every ticket file begins with a YAML frontmatter block:

```yaml
---
id: T3
title: Snapshot tests for build.py argument assembly
status: plan-needed
depends_on: [T2]
---
```

Fields:
- **id** — `T{N}` string, unique, sequential. Never reused.
- **title** — short descriptive title, sentence case, no period.
- **status** — one of the values below.
- **depends_on** — list of ticket ID strings. Empty list `[]` if none.
- **plan** — (optional) filename of the plan file in `agent/plans/`, e.g. `t3-plan.md`. Added when a plan is created during the `plan-needed` phase.

## Status values

Ordered by lifecycle progression:

| Value | Label | Meaning |
|---|---|---|
| `blocked` | Blocked | Cannot start; reason stated in body |
| `design-needed` | Design needed | Open questions must be discussed before planning |
| `plan-needed` | Plan needed | Enter plan mode, write approach, get user approval |
| `ready` | Ready | Approved plan exists, start implementing |
| `done` | Done | Implemented and verified |

## Status transitions

Normal flow: `design-needed` → `plan-needed` → `ready` → `done`

A ticket can enter `blocked` from any status and return to its previous status when unblocked.

A `done` ticket can be reopened to any earlier status if rework is needed.

## File naming

Tickets: `agent/tickets/t{N}-{slug}.md` or `agent/tickets/{epic}/t{N}-{slug}.md` — N is the ticket number (no leading zeros), slug is a lowercase-hyphenated summary.

Plans: `agent/plans/t{N}-plan.md` — one plan file per ticket, created during the `plan-needed` phase.

Examples: `agent/tickets/t4-branch-based-builds.md`, `agent/tickets/ci/t1-linting-ci.md`, `agent/plans/t4-plan.md`

## Epics (directory-based grouping)

An epic is a subdirectory under `agent/tickets/` (e.g., `agent/tickets/ci/`). The directory name IS the epic identity — there is no `epic` frontmatter field on individual tickets. Epic membership is determined solely by which directory a ticket file lives in.

- **Ungrouped tickets stay at root.** Epic membership is optional. Tickets without an epic remain in `agent/tickets/` directly.
- **Optional EPIC.md.** Each epic directory may contain an `EPIC.md` with a title and description. Not required — a bare directory with just ticket files is a valid epic.
- **Shared context files** (like `ci-background.md`) can live in epic directories alongside tickets.
- **Glob pattern for all tickets:** `agent/tickets/**/t*.md` — this recurses into subdirectories.
- **No nesting.** Epics are one level deep. Do not create subdirectories within an epic directory.

## Body structure

After frontmatter, ticket files use this structure:

- **`# T{N}: {title}`** — H1 heading matching the frontmatter
- **`## Goal`** — one-paragraph summary of what this ticket achieves
- **`## Context`** — background, motivation, constraints, prior art
- **`## Key files`** — bulleted list of files this ticket creates/modifies
- **`## Approach`** — brief summary of the implementation strategy (2-5 sentences). If a plan file exists, this summarizes it — the full plan lives in `agent/plans/t{N}-plan.md`.
- **`## Done when`** — bulleted acceptance criteria, split into "Verifiable now" and "Requires manual verification" where applicable

## Plan files

Plan files in `agent/plans/` capture the strategic decisions made during the planning phase. Structure:

- **Context** — why this change is needed (1-2 sentences)
- **Approach** — numbered steps describing what to build and how, with rationale for non-obvious decisions
- **Key files** — files to create and modify, with notes on what changes
- **Verification** — how to confirm the implementation is correct

The plan captures enough for a fresh session to skip exploration and go straight to reading/modifying the right files. It does not need to capture every implementation detail — sessions rebuild that context by reading source files during the warm-up phase.

## Shared context

`agent/tickets/ci/ci-background.md` is shared context for CI-related tickets (T1-T8). It is NOT a ticket — no frontmatter. Shared context files can live in epic directories alongside tickets.

