---
id: T46
title: Add ticket sizing guidance to ticket-format.md
status: design-needed
depends_on: []
---

# T46: Add ticket sizing guidance to ticket-format.md

## Goal

Add guidance to ticket-format.md on when a ticket is too big and should be split, or too small to warrant its own ticket.

## Context

No sizing guidance exists. Some candidate heuristics, none obviously correct:

- **Numeric threshold**: "If Done-when has more than N criteria, consider splitting." Simple but arbitrary — some tickets have many small criteria, some have few massive ones.
- **Session-scoped**: "If the ticket can't be completed in a single /workon session, it's too big." Practical but hard to estimate in advance.
- **Subsystem-scoped**: "If Done-when criteria span multiple unrelated subsystems, split." Catches the worst cases but misses single-subsystem tickets that are just large.
- **Review-scoped**: "If the RED phase would produce more tests than you'd want to review in one batch, the ticket is too big." Ties to the TDD workflow but only applies after you've started.

The inverse (too small) is also unclear. A drive-by rename doesn't need a ticket, but where's the line?

This needs a design discussion before committing to a rule.

## Key files

- `.claude/skills/shared/ticket-format.md`

## Done when

- ticket-format.md has sizing guidance that helps decide when to split or merge tickets
