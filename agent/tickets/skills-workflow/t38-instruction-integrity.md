---
id: T38
title: Referential integrity for skill and ticket references
status: design-needed
depends_on: []
---

# T38: Referential integrity for skill and ticket references

## Goal

Reduce silent failures caused by stale, broken, or ambiguous references in instruction markdown (skills, tickets, shared docs).

## Context

Research in `agent/research/referential-integrity-in-instruction-markdown.md` documents the general problem: instruction markdown contains literal paths, ticket IDs, and function names that go stale silently. Unlike code, there's no compiler to catch broken references — the LLM follows stale instructions confidently.

Specific instances surfaced in the skills audit (`agent/skills-audit.md`):

- **roadmap**: `depends_on` references aren't validated — a typo like `[T99]` silently creates a broken dependency
- **roadmap**: query workflow says "load_tickets() pattern" — ambiguous whether to call the function or replicate its logic
- **roadmap**: import workflow has no duplicate detection against existing tickets
- **backfill-spec**: creates tickets with same numbering as `/roadmap` but doesn't say so

The research doc evaluates several approaches (frontmatter variable interpolation, path linting, convention-based discipline) but concluded no tooling is warranted yet. This ticket reconsiders that decision given the growing volume of cross-references as the ticket count increases.

## Key files

- `agent/research/referential-integrity-in-instruction-markdown.md` — prior research
- `.claude/skills/roadmap/SKILL.md` — multiple reference integrity issues
- `scripts/src/scripts/tickets.py` — could enforce validations programmatically

## Done when

- A decision is made on which mitigation approach to pursue (or to defer again)
- If proceeding: the chosen approach is implemented and the specific issues listed above are resolved
