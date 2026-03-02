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

## Step 2: Draft the spec (internal)

Draft a complete SPEC.md internally following the format in `.claude/skills/shared/spec-format.md`. Do not show the draft to the user — it is working state. Fill in all sections based on what the code reveals:

- **What it does** — derive from the feature's public interface and user-facing behavior
- **Behaviors** — derive from code paths, event handlers, API endpoints, UI interactions. Each bullet should be a testable "When {trigger}, {outcome}" statement.
- **Design decisions** — note choices that seem non-obvious. If you can determine the rationale from context (comments, commit messages, ticket), include it. If not, mark with `[?]` — these become questions in Step 3.
- **Key files** — list the most important files with one-line descriptions
- **Constraints** — include only if notable constraints are evident from the code

## Step 3: Identify open questions

List specific questions about design intent that the code alone cannot answer. Target 3–7 questions.

**What to ask about:**
- The "why" behind non-obvious choices. "The drawer minimum width is 320px — was this chosen for a specific reason, or is it arbitrary?"
- Boundaries and scope. "Search filters by title and ID but not by status. Was status filtering intentionally excluded?"
- Alternatives considered. "You used library X for Y. Were alternatives considered?"
- Missing behaviors. "There's no error handling for failed PATCH requests. Is this intentional, or a gap?"

**What not to ask about:**
- Implementation details that don't surface in the spec. "Why did you use `$derived` instead of `$effect`?" is too low-level.
- Things obvious from the code. "What does the Board component render?" — read the code.

**Guidelines:**
- Group questions by spec section (Behaviors vs Design Decisions) so the user can answer in context.
- Limit to 3–7 questions. More than that and the user disengages.
- Each question should directly affect spec content. If the answer wouldn't change the spec, don't ask.

## Step 4: Ask the questions

Present only the open questions to the user. Do not include the draft spec — the user doesn't need to review it yet. Frame as: "I've drafted the spec internally. Before I write it, I have N questions about design intent."

If the user's answers are ambiguous or incomplete, ask follow-up questions until the design decisions section can be written without `[?]` markers.

## Step 5: Write to disk

Incorporate the user's answers into the draft. Resolve all `[?]` markers. Write the SPEC.md file to the feature directory and offer to `/commit`.

## Step 6: Revise on disk

The user reviews the spec on disk (markdown preview, editor, etc.). If they request changes, make them and offer to commit again. This is where the "user-owned" property is exercised — the user has the final say on content, but reviews it in a proper rendering context rather than in chat.
