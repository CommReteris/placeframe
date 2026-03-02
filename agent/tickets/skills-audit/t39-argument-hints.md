---
id: T39
title: Add argument-hint frontmatter to skills that accept arguments
status: done
depends_on: []
---

# T39: Add argument-hint frontmatter to skills that accept arguments

## Goal

Add `argument-hint` to skill frontmatter so the autocomplete dropdown shows what arguments each skill accepts.

## Context

Several skills accept arguments but the autocomplete menu only shows the skill name and description. The `argument-hint` frontmatter field adds a placeholder hint in the autocomplete dropdown (e.g., `workon [ticket-id]`), making the slash command menu self-documenting. No behavior change — purely a visual cue.

## Key files

- `.claude/skills/workon/SKILL.md` — hint: `[ticket-id]`
- `.claude/skills/roadmap/SKILL.md` — hint: `[create|import|query|reorganize]`
- `.claude/skills/backfill-spec/SKILL.md` — hint: `[directory-path]`
- `.claude/skills/commit/SKILL.md` — hint: `[hint-text]`

## Done when

- All four skills have `argument-hint` in their frontmatter
- Verified hints appear in autocomplete dropdown
