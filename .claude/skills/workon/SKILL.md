---
name: workon
description: Pick up and work on a roadmap ticket.
---

Pick up a ticket from the Placeframe roadmap and work through its lifecycle. Enforces test-driven development during implementation.

Reference docs: `.claude/skills/shared/ticket-format.md` (frontmatter schema, statuses), `.claude/skills/shared/testing.md` (test conventions), `.claude/skills/shared/spec-format.md` (SPEC.md convention).

## 1. Select ticket

Read frontmatter from all `agent/plans/t*.md` files using the `parse_frontmatter()` pattern from `scripts/src/scripts/tickets.py`. If the user specified a ticket (e.g. `/workon T4`), use that one. Otherwise, list tickets grouped by status and ask.

## 2. Read the detail file

Read the ticket's full markdown body. Understand the Goal, Context, Approach, and Done-when criteria.

## 3. Check status and act

- **`blocked`** — Show the blocking reason from the ticket body. Ask if the user wants to unblock (change status and proceed) or pick a different ticket.
- **`design-needed`** — Present the open questions. Discuss with the user until the approach is clear. Update the frontmatter status to `plan-needed`. Proceed to step 4.
- **`plan-needed`** — Enter plan mode. Explore the codebase, write an implementation plan in the ticket's Approach section, get user approval. Update frontmatter status to `ready`. Proceed to step 4.
- **`ready`** — Proceed to step 4 (TDD implementation).
- **`done`** — Inform the user the ticket is done and ask if they want to reopen it.

## 4. TDD implementation cycle

When status is `ready`, implement using Red-Green-Refactor.

### RED phase — write failing tests

1. Read the ticket's "Done when" criteria. Each criterion is the starting point for one or more test cases.
2. **Check for existing SPEC.md.** Identify the primary directory from the ticket's "Key files" section. If a SPEC.md exists there, read it. The Behaviors section contains testable statements about existing functionality. For each behavior that the current ticket modifies or extends: write regression tests that verify the existing behavior still holds (unless the ticket explicitly changes it), and derive new test cases for behaviors the ticket adds or modifies. If the ticket's changes conflict with a spec behavior, flag this as spec drift (see step 6a).
3. Write tests that encode the criteria and any relevant spec behaviors. Add additional tests for edge cases, error handling, and implementation details the criteria don't explicitly mention.
4. Follow the conventions in `.claude/skills/shared/testing.md`: AAA pattern, descriptive names (`test_should_<expected>_when_<condition>`), mock only at system boundaries.
5. Run the tests. Verify they **fail for the right reason** — missing functionality, not syntax errors or import failures. Fix any mechanical issues until all failures are "expected" failures.
6. **STOP. Present the test file(s) to the user and ask them to review the test design.** Do NOT proceed to the GREEN phase until the user approves. Explain what each test covers and why. If any tests derive from SPEC.md behaviors, note which spec behavior they verify.

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

## 6. Spec maintenance

Check if the primary directory (from the ticket's "Key files") has a SPEC.md.

### 6a. Spec drift detection

If a SPEC.md exists, re-read it and compare its Behaviors section against the current code (including changes just implemented). If any spec behaviors no longer match the code:

- **Present each discrepancy** to the user. Format: "SPEC says: {behavior}. Code does: {actual}."
- **Ask the user how to proceed** for each discrepancy: update the spec to match the code (behavior intentionally changed), update the code to match the spec (the code has a bug), or defer (the discrepancy is known and acceptable for now).
- **Never auto-correct** either direction. The user decides.

### 6b. Spec update proposal

If the ticket added new behaviors, modified existing behaviors, or introduced new design decisions, draft proposed updates to the SPEC.md (or a new SPEC.md if none exists and the user wants one). Present the complete proposed SPEC.md — show the full document, not a diff. The user must explicitly approve before any changes are written to disk.

If no SPEC.md exists and the feature is not yet mature enough for a spec, do not pressure the user — simply note that no spec exists and move on.

## 7. Complete

Update the ticket's frontmatter status to `done`. Regenerate `roadmap.md` by running `generate_roadmap(load_tickets())` from `tickets.py` (or updating the roadmap entry manually to match).

## 8. Commit

Offer to `/commit` or `/tidy-commits` as appropriate. Remember: separate prose and code commits.
