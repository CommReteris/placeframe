---
id: T15
title: Create /intake skill
status: done
depends_on: []
---

# T15: Create /intake skill

## Goal

A reusable skill for importing work items from any external source into the roadmap.

## Context

Work items come from many sources — emails, Linear exports, meeting notes, README mentions, user brainstorming sessions. The process is always the same: extract discrete items, deduplicate against the existing roadmap, triage with the user, and create ticket stubs for approved items. This skill codifies that workflow.

## Approach

1. **Create `.claude/skills/shared/ticket-format.md`** — shared reference doc describing the ticket stub format (detail file structure, roadmap entry format, status definitions, T-number assignment). Both `/intake` and `/ticket` read this for consistency.

2. **Create `.claude/skills/intake/SKILL.md`** with this workflow:
   - User provides input: pasted text, a file path, or just describes items verbally.
   - Skill extracts discrete work items from the input.
   - Skill reads `agent/plans/roadmap.md` and actively flags potential overlaps with existing tickets.
   - Skill presents candidates to user for triage (accept, reject, merge with existing).
   - For accepted items: assign next T-number, create stub detail file (`agent/plans/t{n}-{slug}.md`), add entry to `roadmap.md` with status "Design needed".
   - Stub detail files contain: title, goal, context (from the source material), empty approach/done-when sections.

3. **Update `/ticket` skill** to reference the shared `ticket-format.md` for consistency when creating follow-on tickets.

## Key files

- `.claude/skills/intake/SKILL.md` — new skill
- `.claude/skills/shared/ticket-format.md` — shared format reference
- `.claude/skills/ticket/SKILL.md` — minor update to reference shared format

## Done when

- `/intake` appears in available skills list
- Running `/intake` with pasted text extracts items, deduplicates, and creates properly formatted ticket stubs
- Ticket stubs match the format of existing tickets (T1-T14)
- `/ticket` references the shared format doc
