---
id: T68
title: Add provenance tracking to LLM guidance artifacts
status: design-needed
depends_on: []
---

# T68: Add provenance tracking to LLM guidance artifacts

## Goal

Every directive in SPEC.md files and ticket design sections should carry provenance metadata identifying where it came from, so users can audit what they approved vs what was synthesized by the LLM, and future sessions can weigh directives accordingly.

## Context

LLM guidance artifacts (specs, ticket designs) accumulate directives from multiple sources: the user stating something directly, a research document's findings, Claude inferring something during implementation, or a convention derived from observed patterns. Today these all look identical on the page — there's no way to distinguish "the user explicitly requested this" from "Claude added this during backfill-spec and the user didn't object."

This matters for two reasons:

1. **Auditability.** The user should be able to scan a spec or ticket and see which lines represent their explicit intent vs LLM synthesis. The SPEC.md ownership rule (user-owned, requires explicit approval) helps but doesn't distinguish between "user wrote this" and "Claude proposed it and user clicked approve."

2. **Weighting.** A future session reading a spec should treat "user stated directly" differently from "inferred from codebase during backfill." Direct user statements are authoritative; inferences are provisional and should be questioned if they conflict with new information.

CLAUDE.md is out of scope — by convention everything there comes from the user directly, so provenance is uniform.

The primary artifacts that need provenance are:
- **SPEC.md files** — especially those created via `/backfill-spec`, where much of the content is inferred from code
- **Ticket design sections** (Goal, Context, Approach) — where Claude synthesizes context from codebase exploration and user input

Possible provenance categories (non-exhaustive, needs design):
- `user-stated` — user said this directly in conversation
- `user-approved` — Claude proposed, user explicitly approved
- `research-derived` — sourced from a research document in `agent/research/`
- `code-inferred` — inferred from reading existing code during backfill or planning
- `convention-derived` — follows an established project convention

Open questions:
- What annotation format? Inline markers, trailing tags, a parallel metadata section?
- How granular? Per-line, per-bullet, per-section?
- How to avoid the annotations making the files unreadable for humans?
- Should provenance be machine-parseable or purely informational?
- Are there other artifact types beyond specs and tickets that need this?

## Key files

- `.claude/skills/shared/spec-format.md` — spec format convention; would need provenance annotation rules
- `.claude/skills/shared/ticket-format.md` — ticket format; would need provenance rules for design sections
- `.claude/skills/backfill-spec/SKILL.md` — backfill-spec skill; primary producer of code-inferred spec content
- `.claude/skills/workon/SKILL.md` — workon skill; writes ticket design and approach sections
- `.claude/skills/roadmap/SKILL.md` — roadmap skill; creates tickets with user-provided and synthesized content

## Done when

- Provenance categories are defined and documented
- Annotation format is chosen (balancing human readability with machine parseability)
- `spec-format.md` and `ticket-format.md` are updated with provenance conventions
- Skills that produce specs and ticket content are updated to emit provenance annotations
