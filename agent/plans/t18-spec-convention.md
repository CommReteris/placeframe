---
id: T18
title: Add SPEC.md convention and integrate into workon workflow
status: plan-needed
depends_on: []
---

# T18: Add SPEC.md convention and integrate into workon workflow

## Goal

Introduce colocated SPEC.md files as living behavioral specifications for each feature/subsystem, and integrate spec creation and maintenance into the `/workon` skill so that specs are a natural part of the development workflow rather than optional documentation.

## Context

After implementing T16 (kanban board), we discovered that no durable record existed of what was actually built — only the ticket describing what was planned. Post-implementation design refinements (resizable drawer, markdown rendering) were never captured anywhere. If the feature were rebuilt from the ticket alone, the same design deficiencies would recur.

Specs are distinct from tickets: tickets are disposable intent ("build X"), specs are the durable record of what was built and why ("X works like this, these decisions were made"). Specs live with the code, not in the backlog.

The spec is user-owned intent. Claude must never create or modify a SPEC.md without presenting the content and receiving explicit user approval. This rule has no exceptions.

Research into industry patterns (ADRs, Documentation-Driven Development, the Codified Context paper) informed this design. ADRs are too decision-focused, Storybook stories are too visual, READMEs are too loose. We need something behavior-focused that an AI agent can read to understand and reproduce a feature.

The workon skill can branch to shared reference files mid-execution (established pattern: workon already reads `testing.md` and `ticket-format.md`). The backfill and maintenance logic will live in shared files to keep the skill itself compact.

## Key files

- `.claude/skills/shared/spec-format.md` — SPEC.md format convention (parallel to `ticket-format.md`)
- `.claude/skills/shared/spec-backfill.md` — interactive backfill process for reverse-engineering specs from existing code
- `.claude/skills/workon/SKILL.md` — updated with backfill mode detection and spec maintenance step
- `CLAUDE.md` — new project-level rule: never modify specs without user approval

## Approach

To be written during plan mode.

## Done when

### Verifiable now
- `.claude/skills/shared/spec-format.md` exists and defines the SPEC.md format
- `.claude/skills/shared/spec-backfill.md` exists and defines the interactive backfill process
- `/workon` skill detects done tickets with no SPEC.md and enters backfill mode (references `spec-backfill.md`)
- `/workon` skill completion phase includes a spec maintenance step that presents proposed changes and asks user for approval
- `/workon` RED phase derives test cases from existing SPEC.md (when modifying a feature that has one) in addition to ticket "Done when" criteria
- `CLAUDE.md` contains a rule stating SPEC.md files are user-owned and must never be modified without explicit approval
- Backfill flow includes: read code, draft spec, identify open questions, present to user, refine based on feedback
- Spec drift detection: if code doesn't match spec, workon presents discrepancies and asks user how to proceed (never auto-corrects)

### Requires manual verification
- The backfill flow asks useful, targeted questions about design decisions rather than making assumptions
- The spec format captures enough detail to reproduce a feature but isn't so verbose it becomes maintenance burden
