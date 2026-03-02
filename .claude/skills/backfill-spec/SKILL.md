---
name: backfill-spec
description: Retroactively create a SPEC.md for a feature directory that predates the spec convention.
---

Backfill a SPEC.md for a feature directory that has code but no specification. This is a one-time migration process for code that predates the SPEC.md convention. For ongoing spec maintenance, see workon steps 6a/6b.

Takes a directory path as argument: `/backfill-spec apps/sveltekit/board`. If no argument is given, ask the user which directory to backfill.

Backfill is collaborative — it requires user participation to capture design intent that code alone cannot reveal. Follow the format defined in `.claude/skills/shared/spec-format.md`.

**Ownership model during backfill:** The general SPEC.md rule ("present complete content, get explicit approval before writing") does not apply during backfill. In backfill, behaviors are derived from code (factual, not intentional) and design decisions are captured through Q&A. The Q&A process is the approval gate for intent; the on-disk review is the approval gate for the final document. This avoids presenting a wall of unrenderable markdown in chat for the user to "approve."

## Step 1: Read the code

Read the key files in the feature directory. Understand the structure, public interface, and data flow. Read any existing tests. If there is an associated ticket in `agent/plans/`, read it for historical context — but the code is the source of truth for behavior, and the user is the source of truth for intent.

For large subsystems, identify natural sub-features first. If the subsystem has clearly distinct sub-features (e.g., a service with separate extraction, matching, and estimation pipelines), consider whether sub-specs are more appropriate than one monolithic spec. Ask the user if uncertain.

## Step 2: Draft the spec (internal)

Draft a complete SPEC.md internally following the format in `.claude/skills/shared/spec-format.md`. Do not show the draft to the user — it is working state. Fill in all sections based on what the code reveals:

- **What it does** — derive from the feature's public interface and user-facing behavior
- **Behaviors** — derive from code paths, event handlers, API endpoints, UI interactions. Each bullet should be a testable "When {trigger}, {outcome}" statement.
- **Design decisions** — note choices that seem non-obvious. If you can determine the rationale from context (comments, commit messages, ticket), include it. If not, mark with `[?]` — these become questions in Step 3.
- **Key files** — list the most important files with one-line descriptions
- **Constraints** — include only if notable constraints are evident from the code

While drafting, also identify **gaps** — behaviors that seem missing, incomplete, or fragile. Mark each with `[gap]`. These become candidates for new tickets in Step 6.

## Step 3: Identify open questions

List specific questions about design intent that the code alone cannot answer. Collect ALL questions — do not artificially limit the count. For a small feature this might be 3–5 questions; for a large subsystem it could be 30+.

**What to ask about:**
- The "why" behind non-obvious choices. "The drawer minimum width is 320px — was this chosen for a specific reason, or is it arbitrary?"
- Boundaries and scope. "Search filters by title and ID but not by status. Was status filtering intentionally excluded?"
- Alternatives considered. "You used library X for Y. Were alternatives considered?"
- Missing behaviors. "There's no error handling for failed PATCH requests. Is this intentional, or a gap?"

**What not to ask about:**
- Implementation details that don't surface in the spec. "Why did you use `$derived` instead of `$effect`?" is too low-level.
- Things obvious from the code. "What does the Board component render?" — read the code.

**Guidelines:**
- Group questions by topic (e.g., "Auth behavior", "Error handling", "Search/filter") so the user can answer in context.
- Each question should directly affect spec content. If the answer wouldn't change the spec, don't ask.

## Step 4: Ask the questions (in batches)

Present questions in batches of ~5–7, grouped by topic. Frame as: "I've drafted the spec internally. Before I write it, I have N questions about design intent. Here's the first batch."

After each batch:
- Incorporate answers into the internal draft
- Resolve any `[?]` markers the answers address
- Update `[gap]` markers based on whether the user confirms something is a gap or explains it as intentional
- Present the next batch (later batches can be informed by earlier answers — sometimes an answer resolves multiple questions)

If the user's answers are ambiguous or incomplete, ask follow-up questions until the design decisions section can be written without `[?]` markers.

For small features where the total question count is ≤7, a single batch is fine.

## Step 5: Write to disk

Incorporate all answers into the draft. Resolve all `[?]` markers. Write the SPEC.md file to the feature directory and offer to `/commit`.

## Step 6: Create tickets for gaps

Review all confirmed `[gap]` items. For each gap:
1. Create a ticket in `agent/plans/` with the next available T-number, status `design-needed`
2. Update the SPEC.md to reference the ticket ID inline (e.g., "Gap: no live refresh (T22)")

This ensures gaps are tracked as actionable work, not just noted in prose. Offer to `/commit` after creating the tickets and updating the spec.

## Step 7: Revise on disk

The user reviews the spec on disk (markdown preview, editor, etc.). If they request changes, make them and offer to commit again. This is where the "user-owned" property is exercised — the user has the final say on content, but reviews it in a proper rendering context rather than in chat.
