---
name: workon
description: Pick up and work on a roadmap ticket through its full lifecycle (planning, TDD, spec maintenance). Use when the user says "work on T4", "pick up a ticket", or wants to implement a roadmap item.
argument-hint: "[ticket-id]"
---

Pick up a ticket from the Placeframe roadmap and work through its lifecycle. Enforces test-driven development during implementation.

Reference docs: `.claude/skills/shared/ticket-format.md` (frontmatter schema, statuses), `.claude/skills/shared/testing.md` (Python test conventions), `.claude/skills/shared/testing-web.md` (TypeScript test conventions), `.claude/skills/shared/spec-format.md` (SPEC.md convention).

## 1. Select ticket

Read frontmatter from all `agent/tickets/**/t*.md` files. If the user specified a ticket (e.g. `/workon T4`), use that one. Otherwise, list tickets grouped by status and ask.

## 2. Read the detail file

Read the ticket's full markdown body. Understand the Goal, Context, Approach, and Done-when criteria.

If the ticket's frontmatter has a `plan` field, also read the referenced plan file from `agent/plans/`.

## 3. Check status and act

- **`blocked`** — Show the blocking reason from the ticket body. Ask if the user wants to unblock (change status and proceed) or pick a different ticket.
- **`design-needed`** — Present the open questions. Discuss with the user until the approach is clear. Update the ticket's `## Approach` section with the resolved design decisions (so they survive session boundaries), then update the frontmatter status to `plan-needed`. Proceed to step 3a.
- **`plan-needed`** — If the ticket already has a `plan` field (i.e. it was moved back to `plan-needed` for revision), go to step 3c (revise plan). Otherwise go to step 3a (create plan).
- **`ready`** — Go to step 3b (warm up from plan) if the ticket has a `plan` field. Otherwise go directly to step 4 (implement).
- **`in-progress`** — Implementation was started in a previous session. Go to step 3b (warm up from plan) if the ticket has a `plan` field. Otherwise go directly to step 4 (implement). Same as `ready`, but signals that prior work exists on this ticket.
- **`in-review`** — Inform the user the ticket is awaiting their review. Ask if they want to move it to `done` (accept) or back to an earlier status (rework needed).
- **`done`** — Inform the user the ticket is done and ask if they want to reopen it.

### 3a. Create plan (status: `plan-needed`)

Enter plan mode. Explore the codebase and design the implementation approach.

The plan captures **strategic decisions** — what to build, which approach, which files to touch, and why. It does not need to capture every implementation detail. A fresh session reading the plan should be able to skip exploration and go straight to reading the files it needs to modify. It should NOT need to re-discover the architecture or re-evaluate approaches.

**Sizing check.** After exploring but before writing the plan, evaluate the ticket against the sizing heuristics in `ticket-format.md`. If the scope turns out to be larger than the ticket anticipated — the Key Files list is long, the approach requires changes across unrelated subsystems, or the implementation would exceed ~400 lines of meaningful change — stop planning and flag this to the user. Propose a decomposition into smaller tickets. Do not write a plan for an oversized ticket.

Before calling ExitPlanMode:

1. Copy the session plan file verbatim to `agent/plans/t{N}-plan.md`. This is the canonical copy — the session plan file is ephemeral and will be lost. Do not summarize, condense, or rewrite; the repo file must be identical to the session file. The plan should include:
   - **Context**: why this change is needed (1-2 sentences, not a copy of the ticket Goal)
   - **Approach**: numbered steps describing what to build and how, with rationale for non-obvious decisions
   - **Key files**: files to create and modify, with brief notes on what changes in each
   - **Verification**: how to confirm the implementation is correct
2. Add a brief summary to the ticket's `## Approach` section (2-5 sentences describing the strategy — this is a summary, not the plan itself).
3. Add `plan: t{N}-plan.md` to the ticket's frontmatter.
4. Update the ticket's frontmatter status to `ready`.

After ExitPlanMode, proceed to step 3b.

### 3b. Warm up from plan (status: `ready`, plan exists)

Enter plan mode. The goal is to rebuild implementation context, not to re-plan.

1. Read the plan file linked from the ticket's `plan` frontmatter field.
2. Read the source files the plan references — every file listed in the plan's "Key files" section. Build the mental model needed to implement.
3. **Check for staleness.** If anything in the codebase contradicts the plan (files moved, APIs changed, dependencies updated), flag each discrepancy to the user. Ask whether to revise the plan or adjust on the fly.
4. Do NOT write to the plan file or ticket during this phase. The plan is already persisted.

Call ExitPlanMode when you have enough context to implement. Proceed to step 4.

### 3c. Revise plan (status: `plan-needed`, plan already exists)

The ticket was moved back to `plan-needed` after a plan was already created. This means the existing plan needs revision — do NOT assume the status was simply forgotten and skip ahead.

Enter plan mode.

1. Read the existing plan file linked from the ticket's `plan` frontmatter field.
2. Read the source files the plan references to understand current state.
3. **Ask the user what needs to change.** The plan exists but something about it is wrong or incomplete — the user moved it back for a reason. Do not guess; ask.
4. Revise the plan based on the discussion. Update the plan file in `agent/plans/` in place.
5. Update the ticket's `## Approach` section if the strategy changed.
6. Update the ticket's frontmatter status to `ready`.

After ExitPlanMode, proceed to step 3b (warm up) or step 4 (implement) depending on whether you have sufficient context.

## 4. TDD implementation cycle

When status is `ready` or `in-progress`, implement using Red-Green-Refactor. If the ticket is prose-only (skill files, shared docs, tickets — no code changes), skip TDD and make the edits directly.

If the ticket's status is `ready` (not yet `in-progress`), update the frontmatter status to `in-progress` before beginning implementation. This signals to future sessions that work has started on this ticket.

### RED phase — write failing tests

1. Read the ticket's "Done when" criteria. Each criterion is the starting point for one or more test cases.
2. **Check for existing SPEC.md.** Identify the primary directory from the ticket's "Key files" section. If a SPEC.md exists there, read it. The Behaviors section contains testable statements about existing functionality. For each behavior that the current ticket modifies or extends: write regression tests that verify the existing behavior still holds (unless the ticket explicitly changes it), and derive new test cases for behaviors the ticket adds or modifies. If the ticket's changes conflict with a spec behavior, flag this as spec drift (see step 8a).
3. Write tests that encode the criteria and any relevant spec behaviors. Start from the "Done when" criteria and spec behaviors, then add tests for edge cases and error handling implied by those criteria. Tests should encode requirements, not predicted code structure.
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

## 5. Audit conventions

Self-correct the current session's output against counter-training conventions. Skip this step for prose-only tickets.

Read `.claude/skills/shared/audit-conventions.md` for the full criteria list.

1. Run `git diff main...HEAD --name-only` to find files changed by this branch. Filter to code files only (Python, configs, TypeScript) — exclude markdown, skill files, tickets.
2. For each changed code file, run `git diff main...HEAD -- <file>` to see only the branch's changes. Open the full file for context.
3. Review **only the changed lines** against each convention in audit-conventions.md.
   - **Mechanical violations** (decorative comments, abbreviated names, absolute intra-package imports, raw subprocess.run, try/except on run_command): fix in place.
   - **Judgment violations** (inlining candidates, unnecessary abstractions): note them briefly when presenting the commit for user review. Do not auto-fix.
4. If pre-existing violations are noticed in surrounding code (not introduced by this branch), record them in the ticket's `## Observations` section. Do not fix them.

## 6. Verify

Run the full verification suite from the ticket's "Done when" section:
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run basedpyright` (for new/modified files)
- `uv run pytest`
- If the ticket touches TypeScript/SvelteKit code, also run `pnpm --dir <app-dir> check` and `pnpm --dir <app-dir> lint` (e.g. `pnpm --dir apps/sveltekit/board check`)
- Any ticket-specific checks listed under "Verifiable now"

Report which passed and which failed. List any "Requires manual verification" items.

## 7. Capture learnings

Re-read the ticket's `## Log` section. For each failure or pivot recorded:

1. **Is it generalizable?** Ask: "Would a future session working on a different ticket hit this same wall?" Skip anything that's purely ticket-specific (e.g. a typo in the test, a one-off API misunderstanding).
2. **Where should it live?** For each generalizable item, identify the destination:
   - **CLAUDE.md** — conventions, rules, or pitfalls that apply project-wide (e.g. "SvelteSet works but SvelteMap doesn't for template reactivity")
   - **`.claude/skills/shared/testing.md` or `testing-web.md`** — testing patterns or E2E gotchas (e.g. "must wait for hydration before interactive tests")
   - **A skill file** — if the learning reveals a gap in a skill's instructions
   - **A SPEC.md design decision** — if the learning explains a non-obvious architectural choice
3. **Present proposals to the user.** List each item with its proposed destination. Do not write anything until the user approves. Format: one line per item — what the insight is, where it should go.
4. **Write approved items.** For each approved item, add it to the appropriate file. Keep additions concise — a sentence or two, same style as surrounding content.

If the log says "Clean implementation, no issues," skip this step entirely.

## 8. Spec maintenance

Check if the primary directory (from the ticket's "Key files") has a SPEC.md.

### 8a. Spec drift detection

If a SPEC.md exists, re-read it and compare its Behaviors section against the current code (including changes just implemented). If any spec behaviors no longer match the code:

- **Present each discrepancy** to the user. Format: "SPEC says: {behavior}. Code does: {actual}."
- **Ask the user how to proceed** for each discrepancy: update the spec to match the code (behavior intentionally changed), update the code to match the spec (the code has a bug), or defer (the discrepancy is known and acceptable for now).
- **Never auto-correct** either direction. The user decides.

### 8b. Spec update proposal

If the ticket added new behaviors, modified existing behaviors, or introduced new design decisions, draft proposed updates to the SPEC.md (or a new SPEC.md if none exists and the user wants one). Visual changes (transitions, hover states, focus rings, spacing, typography) are behaviors — include them in spec proposals. Present the complete proposed SPEC.md — show the full document, not a diff. The user must explicitly approve before any changes are written to disk.

If no SPEC.md exists and the feature is not yet mature enough for a spec, do not pressure the user — simply note that no spec exists and move on.

## 9. Submit for review

Update the ticket's frontmatter status to `in-review`.

Add a `## Log` section to the ticket body. This section records what was tried and failed during implementation, and what was changed to resolve each failure:

- For each failure encountered (test failures, wrong approaches, dead ends): describe what was tried, why it failed, and what was changed to keep going.
- Only record failures and pivots — not a summary of what was built or a restatement of the approach.
- If implementation was clean with no failures, write "Clean implementation, no issues."

Add a `## Observations` section to the ticket body. This section records pre-existing issues noticed in surrounding code during implementation — things not introduced by this branch and not fixed in this ticket:

- Terse entries: file path + what was observed.
- If nothing was noticed, write "No pre-existing issues noticed."

Both sections are always present once a ticket reaches `in-review`.

## 10. Commit

Offer to `/commit`. Remember: separate prose and code commits.
