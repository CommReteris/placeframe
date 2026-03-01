---
name: workon
description: Pick up and work on a roadmap ticket.
---

Pick up a ticket from the Placeframe roadmap and work through its lifecycle. Enforces test-driven development during implementation.

Reference docs: `.claude/skills/shared/ticket-format.md` (frontmatter schema, statuses), `.claude/skills/shared/testing.md` (test conventions).

## 1. Select ticket

Read frontmatter from all `agent/plans/t*.md` files using the `parse_frontmatter()` pattern from `scripts/src/scripts/tickets.py`. If the user specified a ticket (e.g. `/workon T4`), use that one. Otherwise, list tickets grouped by status and ask.

## 2. Read the detail file

Read the ticket's full markdown body. Understand the Goal, Context, Approach, and Done-when criteria.

## 3. Check status and act

- **`blocked`** — Show the blocking reason from the ticket body. Ask if the user wants to unblock (change status and proceed) or pick a different ticket.
- **`design-needed`** — Present the open questions. Discuss with the user until the approach is clear. Update the frontmatter status to `plan-needed`. Proceed to step 4.
- **`plan-needed`** — Enter plan mode. Explore the codebase, write an implementation plan in the ticket's Approach section, get user approval. Update frontmatter status to `ready`. Proceed to step 4.
- **`ready`** — Proceed to step 4 (TDD implementation).
- **`done`** — Inform the user. Ask if they want to reopen.

## 4. TDD implementation cycle

When status is `ready`, implement using Red-Green-Refactor.

### RED phase — write failing tests

1. Read the ticket's "Done when" criteria. Each criterion is the starting point for one or more test cases.
2. Write tests that encode the criteria. Add additional tests for edge cases, error handling, and implementation details the criteria don't explicitly mention.
3. Follow the conventions in `.claude/skills/shared/testing.md`: AAA pattern, descriptive names (`test_should_<expected>_when_<condition>`), mock only at system boundaries.
4. Run the tests. Verify they **fail for the right reason** — missing functionality, not syntax errors or import failures. Fix any mechanical issues until all failures are "expected" failures.
5. **STOP. Present the test file(s) to the user and ask them to review the test design.** Do NOT proceed to the GREEN phase until the user approves. Explain what each test covers and why.

### GREEN phase — implement minimally

1. Write the minimum code to make all tests pass.
2. Run tests after each meaningful change. Verify passing tests stay passing — never break a passing test.
3. No over-engineering, no features beyond what tests require. If a test doesn't ask for it, don't build it.

### REFACTOR phase — clean up

1. Improve the implementation while keeping all tests green.
2. Apply project code conventions: `uv run ruff format .`, `uv run ruff check .`, `uv run basedpyright`.
3. Remove duplication, improve naming, simplify logic. Inline aggressively per CLAUDE.md conventions.

## 5. Verify

Run the full verification suite from the ticket's "Done when" section:
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run basedpyright` (for new/modified files)
- `uv run pytest`
- Any ticket-specific checks listed under "Verifiable now"

Report which passed and which failed. List any "Requires manual verification" items.

## 6. Complete

Update the ticket's frontmatter status to `done`. Regenerate `roadmap.md` by running `generate_roadmap(load_tickets())` from `tickets.py` (or updating the roadmap entry manually to match).

## 7. Commit

Offer to `/commit` or `/tidy-commits` as appropriate. Remember: separate prose and code commits.
