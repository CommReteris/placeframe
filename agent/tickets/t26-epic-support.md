---
id: T26
title: Add epic support to ticket system
status: design-needed
depends_on: []
---

# T26: Add epic support to ticket system

## Goal

Add an "epic" concept to the ticketing system so that large groups of related tickets (e.g., all action items from a skills audit) can be organized under a parent theme without losing the flat-file simplicity of the current system.

## Context

The skills audit (`agent/skills-audit.md`) produced ~15 discrete action items that each warrant their own ticket. The ticket list is about to grow from 25 to 40+, and without grouping, `/roadmap query` output becomes unwieldy. Epics provide that grouping.

The current system uses flat markdown files with YAML frontmatter (`id`, `title`, `status`, `depends_on`). Any epic support should extend this rather than replace it.

## Key files

- `.claude/skills/shared/ticket-format.md` — frontmatter schema, status values
- `scripts/src/scripts/tickets.py` — `load_tickets()`, `update_ticket_status()`, parsing
- `.claude/skills/roadmap/SKILL.md` — create/import/query/reorganize workflows
- `.claude/skills/workon/SKILL.md` — ticket lifecycle

## Approach

TBD — needs design discussion. Options include: a frontmatter `epic` field on tickets, standalone epic files, or a simple tag/label system.

## Done when

- Tickets can be associated with an epic
- `/roadmap query` can filter and group by epic
- `tickets.py` supports epic field in parsing and filtering
- `ticket-format.md` documents the epic convention
- Existing tickets continue to work unchanged (epic is optional)
