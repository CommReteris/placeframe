# Spec Backfill Process

Interactive process for reverse-engineering a SPEC.md from existing code. Triggered when the `/workon` skill encounters a done ticket whose feature directory has no SPEC.md.

Backfill is collaborative — it requires user participation to capture design intent that code alone cannot reveal. Follow the format defined in `spec-format.md`.

## Step 1: Read the code

Read the key files in the feature directory. Understand the structure, public interface, and data flow. Read any existing tests. Read the originating ticket for historical context — but the code is the source of truth for behavior, and the user is the source of truth for intent.

## Step 2: Draft the spec

Write a complete SPEC.md following the format in `spec-format.md`. Fill in all sections based on what the code reveals:

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

## Step 4: Present to user

Show the complete draft spec and the open questions together in a single message. The user reviews the spec content and answers the questions.

This is the approval gate — nothing is written to disk until the user approves. Make this explicit: "Here's the draft SPEC.md and some questions. Once you're happy with the content, I'll write it."

## Step 5: Refine and write

Incorporate the user's feedback into the draft. If the user requests changes, update the draft and present the full updated spec again — do not show a diff, show the complete document.

Once the user approves, write the SPEC.md file to the feature directory. Offer to `/commit`.
