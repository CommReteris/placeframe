---
id: T67
title: Convention audit bypassed when code is written outside workon skill
status: design-needed
depends_on: []
---

# T67: Convention audit bypassed when code is written outside workon skill

## Goal

Ensure the counter-training convention audit (`audit-conventions.md`) runs on all code changes, not just those initiated through the `/workon` skill.

## Context

The audit step currently lives inside the `/workon` skill. But code gets written through other paths — e.g., `/roadmap` query leads to investigation, which leads to planning, which leads to implementation. The audit step is coupled to a specific skill invocation, not to the act of writing code. This was discovered during T62 work: all code was written without an audit pass because `/workon` was never invoked.

The audit conventions are specifically labeled "counter-training" — they catch things that conflict with LLM training priors (abbreviated variable names, unnecessary abstractions, decorative comments). These are exactly the mistakes most likely to happen when the audit is skipped.

Candidate solutions discussed:
1. **Add to CLAUDE.md** — always loaded, but adds process noise to an already long file
2. **Add to the commit skill** — natural chokepoint, every code path converges on `/commit`. Already reads `commit-style.md`, same pattern. Adds latency to every commit.
3. **Shared pre-commit fragment** — like `git-preflight.md`, referenced by any skill that offers to commit. Requires each skill author to remember to include it.

Option 2 (commit skill) seemed most robust in initial discussion, but no decision was made.

## Done when

- Convention audit runs on changed lines regardless of which skill (or no skill) initiated the work
- No realistic workflow path can produce a commit without the audit having run
