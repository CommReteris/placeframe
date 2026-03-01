# T17: /workon skill with TDD workflow and frontmatter system

## Goal

Replace the `/ticket` skill with `/workon` — a ticket implementation skill that enforces test-driven development through explicit RED/GREEN/REFACTOR phases. Add YAML frontmatter to all ticket files as the machine-readable source of truth. Create shared documentation for ticket format and testing conventions.

## Context

The current `/ticket` skill reads status from `roadmap.md` prose and has no testing discipline — it jumps straight to implementation. This produces code that works but isn't verified by tests, and ticket status updates require manual roadmap editing.

YAML frontmatter on each ticket file gives programmatic access to status and dependencies. The `/workon` skill reads frontmatter, drives work through lifecycle phases (design → plan → implement → verify → done), and enforces TDD during the implementation phase: write failing tests first (RED), implement minimally to pass (GREEN), then clean up (REFACTOR). A human review gate after the RED phase ensures tests correctly encode the ticket's acceptance criteria before any implementation begins.

This is prerequisite infrastructure for T16 (kanban board), which visualizes the frontmatter data. The `/roadmap` skill (ticket creation, querying, reorganization) remains in T16's scope.

### Why TDD in the skill, not as a separate tool

Research into Claude Code TDD workflows (tdd-guard, multi-agent architectures, mattpocock/skills, obra/superpowers) shows a spectrum from CLAUDE.md rules (unreliable — ~20% compliance) to hook-based enforcement (heavyweight). The sweet spot for a single-developer project: explicit phase gates in the skill itself with a human review pause after test design. This catches the critical failure mode (bad tests → bad implementation) without the ceremony of PreToolUse hooks or multi-agent context isolation.

## Key files

- `agent/plans/t*.md` — all ticket files (add frontmatter)
- `scripts/src/scripts/tickets.py` — shared ticket module (already exists, needs review)
- `.claude/skills/workon/SKILL.md` — new (replaces `.claude/skills/ticket/SKILL.md`)
- `.claude/skills/shared/ticket-format.md` — new shared format reference
- `.claude/skills/shared/testing.md` — new test conventions guide
- `.claude/skills/ticket/` — delete
- `agent/plans/roadmap.md` — regenerated from frontmatter

## Approach

### 1. Add frontmatter to all ticket files

Add YAML frontmatter block to the top of each `agent/plans/t*.md` file:

```yaml
---
id: T3
title: Snapshot tests for build.py argument assembly
status: plan-needed
depends_on: [T2]
---
```

Schema: `id` (string), `title` (string), `status` (one of: blocked, design-needed, plan-needed, ready, done), `depends_on` (list of ticket ID strings). Status and dependency values extracted from current `roadmap.md`. `ci-background.md` is shared context, not a ticket — no frontmatter.

### 2. Review and finalize tickets.py

The module already exists at `scripts/src/scripts/tickets.py`. Review for correctness against the frontmatter schema, ensure `generate_roadmap()` produces output matching the current roadmap format, and verify all functions work with the actual ticket files.

### 3. Create shared ticket format reference

New file `.claude/skills/shared/ticket-format.md`. Documents: frontmatter schema, status values and meanings, status transitions, file naming convention (`t{N}-{slug}.md`), ticket body structure (Goal, Context, Approach, Done when), `depends_on` conventions.

### 4. Create shared testing conventions

New file `.claude/skills/shared/testing.md`. Detailed test style guide covering:

- **Framework**: pytest, with `uv run pytest` from repo root
- **File placement**: tests alongside the code they test (e.g. `docker/api/tests/`, `scripts/tests/`)
- **Naming**: `test_should_<expected>_when_<condition>` for test functions, `Test<Unit>` for classes
- **Pattern**: Arrange-Act-Assert (AAA), one logical assertion per test
- **Mocking**: mock only at system boundaries (external APIs, databases, filesystem, time/randomness). Never mock internal collaborators. Use dependency injection for testability.
- **Fixtures**: prefer factory functions over complex fixture chains. Fixtures for shared setup only.
- **Parametrize**: use `@pytest.mark.parametrize` for data-driven tests, not copy-pasted test functions
- **Coverage**: no numeric target. Tests encode acceptance criteria, not line coverage.

### 5. Create /workon skill

New file `.claude/skills/workon/SKILL.md`. Workflow:

1. **Select ticket**: Read frontmatter from all `agent/plans/t*.md` files. If ticket ID provided (e.g. `/workon T4`), use it. Otherwise, list tickets by status and ask user.

2. **Check status and act**:
   - `blocked` — show reason, ask if user wants to unblock
   - `design-needed` — discuss open questions with user, update status to `plan-needed` when resolved
   - `plan-needed` — enter plan mode, write implementation plan in the ticket's Approach section, update status to `ready` when user approves
   - `ready` — enter TDD implementation cycle (step 3)
   - `done` — inform user, ask if they want to reopen

3. **TDD implementation cycle** (when status is `ready`):

   **RED phase:**
   - Read the ticket's "Done when" criteria as the starting point for test design
   - Write failing tests that encode each criterion, plus additional tests for edge cases, error handling, and implementation details the criteria don't explicitly cover
   - Run tests — verify they FAIL for the right reason (missing functionality, not syntax/import errors)
   - **STOP and present tests to user for review.** Do not proceed until user approves test design.

   **GREEN phase:**
   - Implement the minimum code to make all tests pass
   - Run tests after each meaningful change — verify passing tests stay passing
   - No over-engineering, no features beyond what tests require

   **REFACTOR phase:**
   - Clean up implementation while keeping all tests green
   - Apply project code conventions (ruff format, basedpyright)
   - Remove duplication, improve naming, simplify logic

4. **Verify**: Run full verification suite — `uv run ruff check .`, `uv run ruff format --check .`, `uv run basedpyright`, `uv run pytest`

5. **Complete**: Update ticket frontmatter status to `done`. Regenerate `roadmap.md`.

6. **Commit**: Offer to `/commit` the work.

### 6. Delete old /ticket skill

Remove `.claude/skills/ticket/` directory entirely.

### 7. Regenerate roadmap.md

Run `generate_roadmap()` from `tickets.py` to produce `roadmap.md` from the new frontmatter data. Verify the output matches the current roadmap content (same tickets, same statuses, same dependencies).

## Done when

- All ticket files (t1 through t17) have valid YAML frontmatter with correct id, title, status, and depends_on
- `roadmap.md` is regenerated from frontmatter and matches current ticket states
- `/workon` skill exists at `.claude/skills/workon/SKILL.md` with RED/GREEN/REFACTOR phases
- `/workon` references shared `ticket-format.md` and `testing.md`
- `.claude/skills/shared/ticket-format.md` documents the frontmatter schema
- `.claude/skills/shared/testing.md` documents test conventions (naming, AAA, mocking boundaries, fixtures, parametrize)
- `.claude/skills/ticket/` is deleted
- `uv run ruff check .` passes
- `uv run ruff format --check .` passes
- `scripts/src/scripts/tickets.py` correctly parses all frontmatter files
- T16 updated to depend on T17 and scoped to kanban board UI only
