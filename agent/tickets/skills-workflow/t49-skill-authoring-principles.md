---
id: T49
title: Create skill-authoring principles reference
status: in-review
depends_on: []
---

# T49: Create skill-authoring principles reference

## Goal

Create a shared reference document (`.claude/skills/shared/skill-authoring.md`) that captures principles for writing and modifying skills. Skills and CLAUDE.md would direct Claude to reference it when creating or updating skills.

## Context

The skills audit and ticket interview surfaced several skill-authoring insights that currently live only in memory files or commit history:

- Examples in skill prose are safe for formulaic outputs, risky for high-variance outputs (the overfitting tradeoff)
- Don't write reference implementations for Claude to read — if no code imports it, it's dead code
- Skill prose length matters — every token costs context window budget on every invocation
- One gate per skill (the permission strategy from allow-tool)
- Progressive disclosure: metadata layer (~100 words) → primary content (<500 lines) → supplementary files (on demand)

Upstream best practices (from Anthropic docs and community) also apply:
- Write descriptions in third person, make them "pushy" for reliable triggering
- Use imperative form in instructions
- Explain the "why" behind instructions
- Keep references one level deep from SKILL.md
- Generalize from feedback rather than overfitting to specific examples

This document would be the authoritative reference for "how to write a good skill in this project," combining project-specific conventions with upstream best practices.

## Approach

Research-backed, prose-only. Created skill-authoring.md covering: cost model (how descriptions/bodies/CLAUDE.md consume context), the CLAUDE.md-vs-skill boundary, description writing for reliable activation, the degrees-of-freedom framework for instruction specificity, progressive disclosure architecture, example usage tradeoffs, and a concrete anti-patterns checklist. CLAUDE.md gets a one-line directive to read it when touching skill files.

## Key files

- `.claude/skills/shared/skill-authoring.md` — new: skill authoring principles
- `.claude/skills/shared/README.md` — updated: added skill-authoring.md to the index
- `CLAUDE.md` — updated: one-line directive to read skill-authoring.md when editing skills

## Done when

- `skill-authoring.md` exists with clear, concise principles
- CLAUDE.md or a skill directs Claude to reference it when creating/modifying skills
- Memory file insights are absorbed into the document (and removed from memory)

## Log

Memory files referenced in the ticket (`/root/.claude/projects/-workspace/memory/MEMORY.md`) no longer exist — insights were already captured in the ticket's Context section. All listed insights are covered in the new document. No other issues.
