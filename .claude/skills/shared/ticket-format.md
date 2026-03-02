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

`agent/plans/t{N}-{slug}.md` — N is the ticket number (no leading zeros), slug is a lowercase-hyphenated summary.

Examples: `t4-branch-based-builds.md`, `t17-workon-tdd.md`

## Body structure

After frontmatter, ticket files use this structure:

- **`# T{N}: {title}`** — H1 heading matching the frontmatter
- **`## Goal`** — one-paragraph summary of what this ticket achieves
- **`## Context`** — background, motivation, constraints, prior art
- **`## Key files`** — bulleted list of files this ticket creates/modifies
- **`## Approach`** — numbered implementation steps with H3 subsections
- **`## Done when`** — bulleted acceptance criteria, split into "Verifiable now" and "Requires manual verification" where applicable

## Shared context

`agent/plans/ci-background.md` is shared context for CI-related tickets (T1-T8). It is NOT a ticket — no frontmatter.

## Programmatic access

`scripts/src/scripts/tickets.py` provides:
- `load_tickets()` — parse all ticket files, return list of Ticket dataclass instances
- `update_ticket_status(ticket_id, new_status)` — update frontmatter in place
