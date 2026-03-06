---
id: T59
title: Add convention audit step to /workon workflow
status: in-review
depends_on: []
plan: t59-plan.md
---

# T59: Add convention audit step to /workon workflow

## Goal

Catch CLAUDE.md convention violations that conflict with LLM training priors before code is committed, by adding an automated audit step to the `/workon` implementation workflow.

## Context

AI-generated code reliably violates certain project conventions because they conflict with patterns dominant in training data. The "inline aggressively" rule is the clearest example — LLMs default to extracting functions and naming everything, which is the opposite of what this project asks. Other counter-training conventions: no decorative comments, no unnecessary abstractions, no gratuitous docstrings, full-word variable names.

These violations persist despite clear CLAUDE.md instructions because generation-time priors are too strong. A post-generation review step is more reliable because *identifying* violations is fundamentally easier than *avoiding* them during generation — the reviewer has no competing creative pressure.

**The audit is self-correction, not a codebase sweep.** It examines only lines introduced or modified by the current branch's diff. Pre-existing violations in surrounding code are not fixed — they are noted in the ticket's `## Observations` section for future `/audit` sweeps. This keeps the step focused on the current session's output.

**Mechanical vs. judgment violations.** Obvious mechanical violations (abbreviated names, `# ---` dividers, decorative comments, absolute intra-package imports) are fixed in place. Judgment calls (whether to inline a variable, whether an abstraction is unnecessary) are flagged for the user to see at commit review, not auto-fixed.

This ticket creates three artifacts:

1. **A shared criteria doc** (`.claude/skills/shared/audit-conventions.md`) listing the specific conventions that conflict with training, with detection guidance and before/after examples. This doc is also consumed by the `/audit` skill (T58) as a criteria doc.

2. **A new step in `/workon`** before Verify (so linting/formatting runs on the post-audit code) that audits changed files against the criteria doc and fixes violations before committing.

3. **A `## Observations` section in ticket format** (`ticket-format.md`) — a required section (like Log) that records pre-existing issues noticed in surrounding code during implementation. States "No pre-existing issues noticed." when empty.

## Key files

- `.claude/skills/shared/audit-conventions.md` — new criteria doc
- `.claude/skills/workon/SKILL.md` — add audit step, renumber subsequent steps
- `.claude/skills/shared/ticket-format.md` — add Observations section to body structure

## Done when

- `audit-conventions.md` exists with detection guidance and before/after examples for each counter-training convention
- `/workon` has an audit step before Verify (between Refactor and Verify)
- The audit step diffs the branch against main to scope changes — only lines introduced or modified by the current branch are flagged/fixed
- Mechanical violations are fixed in place; judgment calls are flagged only
- Pre-existing violations in surrounding code are recorded in the ticket's `## Observations` section, not fixed
- `ticket-format.md` documents the `## Observations` section as a required ticket section (like Log), present once implementation begins
- Step numbering in workon is consistent after insertion

## Log

Clean implementation, no issues.

## Observations

No pre-existing issues noticed.
