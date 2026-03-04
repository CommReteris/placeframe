# Ticket Format Reference

## Contents

- [Frontmatter schema](#frontmatter-schema)
- [Status values](#status-values)
- [Status transitions](#status-transitions)
- [File naming](#file-naming)
- [Epics](#epics-directory-based-grouping)
- [Body structure](#body-structure)
- [Plan files](#plan-files)
- [Ticket sizing](#ticket-sizing)
- [Shared context](#shared-context)

## Frontmatter schema

Every ticket file begins with a YAML frontmatter block:

```yaml
---
id: T3
title: Snapshot tests for build.py argument assembly
status: plan-needed
depends_on: [T2]
---
```

Fields:
- **id** — `T{N}` string, unique, sequential. Never reused.
- **title** — short descriptive title, sentence case, no period.
- **status** — one of the values below.
- **depends_on** — list of ticket ID strings. Empty list `[]` if none.
- **plan** — (optional) filename of the plan file in `agent/plans/`, e.g. `t3-plan.md`. Added when a plan is created during the `plan-needed` phase.

## Status values

Ordered by lifecycle progression:

| Value | Label | Meaning |
|---|---|---|
| `blocked` | Blocked | Cannot start; reason stated in body |
| `design-needed` | Design needed | Open questions must be discussed before planning |
| `plan-needed` | Plan needed | Enter plan mode, write approach, get user approval |
| `ready` | Ready | Approved plan exists, start implementing |
| `in-progress` | In progress | Implementation actively underway (set by workon skill) |
| `in-review` | In review | Implementation complete, awaiting human review |
| `done` | Done | Reviewed and accepted by a human |

## Status transitions

Normal flow: `design-needed` → `plan-needed` → `ready` → `in-progress` → `in-review` → `done`

Only a human moves a ticket from `in-review` to `done`. The workon skill moves tickets to `in-review` after implementation is verified.

A ticket can enter `blocked` from any status and return to its previous status when unblocked.

A `done` ticket can be reopened to any earlier status if rework is needed.

## File naming

Tickets: `agent/tickets/t{N}-{slug}.md` or `agent/tickets/{epic}/t{N}-{slug}.md` — N is the ticket number (no leading zeros), slug is a lowercase-hyphenated summary.

Plans: `agent/plans/t{N}-plan.md` — one plan file per ticket, created during the `plan-needed` phase.

Examples: `agent/tickets/t4-branch-based-builds.md`, `agent/tickets/ci/t1-linting-ci.md`, `agent/plans/t4-plan.md`

## Epics (directory-based grouping)

An epic is a subdirectory under `agent/tickets/` (e.g., `agent/tickets/ci/`). The directory name IS the epic identity — there is no `epic` frontmatter field on individual tickets. Epic membership is determined solely by which directory a ticket file lives in.

- **Ungrouped tickets stay at root.** Epic membership is optional. Tickets without an epic remain in `agent/tickets/` directly.
- **Optional EPIC.md.** Each epic directory may contain an `EPIC.md` with a title and description. Not required — a bare directory with just ticket files is a valid epic.
- **Shared context files** (like `ci-background.md`) can live in epic directories alongside tickets.
- **Glob pattern for all tickets:** `agent/tickets/**/t*.md` — this recurses into subdirectories.
- **No nesting.** Epics are one level deep. Do not create subdirectories within an epic directory.

## Body structure

After frontmatter, ticket files use this structure:

- **`# T{N}: {title}`** — H1 heading matching the frontmatter
- **`## Goal`** — one-paragraph summary of what this ticket achieves
- **`## Context`** — background, motivation, constraints, prior art
- **`## Key files`** — bulleted list of files this ticket creates/modifies
- **`## Approach`** — brief summary of the implementation strategy (2-5 sentences). If a plan file exists, this summarizes it — the full plan lives in `agent/plans/t{N}-plan.md`.
- **`## Done when`** — bulleted acceptance criteria, split into "Verifiable now" and "Requires manual verification" where applicable
- **`## Next step`** — one or two sentences describing the concrete next action for this ticket. Required for `blocked` and `design-needed` statuses. Required for `in-progress` if work has spanned sessions. Optional elsewhere (status tells the story: `ready` = implement the plan, `in-review` = awaiting review). Removed when the ticket moves to `in-review`. Content should be specific enough that a fresh session knows what to do without re-reading the full conversation history. For `design-needed`, this often captures a decision with options: "Decide between X and Y — see Research for trade-offs."
- **`## Log`** — records what was tried and failed during implementation, and what was changed to resolve each failure. Always present once implementation begins. If implementation was clean with no issues, state that. This section is written by the workon skill when moving a ticket to `in-review`.
- **`## Observations`** — records pre-existing issues noticed in surrounding code during implementation — things not introduced by this branch and not fixed in this ticket. Terse entries: file path + what was observed. Always present once implementation begins. If nothing was noticed, state "No pre-existing issues noticed." Written by the workon skill alongside the Log section.

## Plan files

Plan files in `agent/plans/` capture the strategic decisions made during the planning phase. Structure:

- **Context** — why this change is needed (1-2 sentences)
- **Approach** — numbered steps describing what to build and how, with rationale for non-obvious decisions
- **Key files** — files to create and modify, with notes on what changes
- **Verification** — how to confirm the implementation is correct

The plan captures enough for a fresh session to skip exploration and go straight to reading/modifying the right files. It does not need to capture every implementation detail — sessions rebuild that context by reading source files during the warm-up phase.

## Ticket sizing

Four constraints determine whether a ticket is the right size. Ordered by durability — the first two are permanent, the last two relax as tooling improves.

### Too big

A ticket is too big if it violates any of these:

1. **Reviewability.** The output must be reviewable in one focused human pass — roughly 400 lines of meaningful change and under 60 minutes of review time. If the reviewer would need to context-switch between unrelated concerns, the ticket is too big. (Grounded in the SmartBear/Cisco code review study: defect detection drops sharply past ~400 lines.)

2. **Atomicity.** The change must be describable in one sentence and revertable as a unit. Apply the one-sentence test: if the description requires "and" joining two unrelated actions ("add auth and refactor the DB layer"), it is multiple tickets. If the "and" joins coupled actions ("add sizing rules and enforce them in skills"), apply the coupling test: **would either half ship independently and be useful?** If yes, split. If no, keep — they are one ticket.

3. **Recoverability.** If a session fails mid-ticket, restarting from scratch should not be painful. A ticket should be completable in a single agent session without context compaction. If the scope is large enough that losing a session means losing hours of work, split.

4. **Context capacity.** The agent must hold the ticket's Key Files, implementation, and tests in working memory without degradation. If the Key Files section lists more files than can be read and understood alongside the implementation work, the ticket is too big. (Agent success rates are 70-80% for tasks a skilled human completes in 1-2 hours, dropping below 20% for 4+ hour tasks per METR's HCAST benchmark.)

Examples of too-big tickets: "Add auth and refactor the database layer" (two unrelated concerns). "Rewrite the localizer service" (unbounded scope, 1000+ lines). "Add CI for linting, tests, and Docker builds" (three independent pipelines — split into one ticket each).

**When you discover a ticket is too big during planning:** stop planning, propose a decomposition to the user, create the new tickets, and update dependencies. Do not barrel ahead into a large implementation.

### Too small

A change does not need a ticket if it involves **no design decisions and no review value** — the ticket ceremony (frontmatter, context, plan, done-when) exists to support decisions. Examples: renaming a variable, fixing a typo, updating a version number, adding a missing import. Just make the change directly.

If several too-small changes are thematically related, they can be grouped into one ticket — but only if the group itself passes the atomicity test (one sentence, one reviewable concern).

## Shared context

`agent/tickets/ci/ci-background.md` is shared context for CI-related tickets (T1-T8). It is NOT a ticket — no frontmatter. Shared context files can live in epic directories alongside tickets.

