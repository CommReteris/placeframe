---
id: T46
title: Add ticket sizing discipline — rules, creation check, planning escape hatch
status: in-review
depends_on: []
---

# T46: Add ticket sizing discipline — rules, creation check, planning escape hatch

## Goal

Add sizing guidance to ticket-format.md and wire enforcement into the roadmap (creation) and workon (planning) skills.

## Context

No sizing guidance exists. After research (agent/research/) and design discussion, settled on four structural constraints grounded in empirical evidence rather than arbitrary thresholds: reviewability, atomicity, recoverability, and context capacity. Also defined a coupling test to disambiguate the common case where individual changes are too small but naturally belong together, and a "too small" heuristic based on whether design decisions exist.

## Approach

Prose-only, three files. Write the sizing rules as a new section in ticket-format.md. Add a sizing check step to the roadmap skill's Create and Import workflows. Add a "ticket too big" escape hatch to workon's planning phase (step 3a). All three reference ticket-format.md as the single source of truth for the rules themselves.

## Key files

- `.claude/skills/shared/ticket-format.md` — new "Ticket sizing" section
- `.claude/skills/roadmap/SKILL.md` — sizing check in Create and Import workflows
- `.claude/skills/workon/SKILL.md` — escape hatch in planning phase

## Done when

- ticket-format.md has a "Ticket sizing" section with too-big and too-small heuristics, including the coupling test for borderline cases
- roadmap skill checks proposed scope against sizing heuristics during Create and Import, proposing splits when appropriate
- workon skill flags oversized tickets discovered during planning and proposes splitting before proceeding

## Log

Clean implementation, no issues.
