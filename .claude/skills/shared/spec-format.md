# SPEC.md Format Convention

## Purpose

Specs are distinct from tickets. Tickets are disposable intent ("build X"). Specs are the durable record of what was built and why ("X works like this, these decisions were made"). Tickets live in the backlog (`agent/tickets/`); specs live with the code they describe.

A spec captures enough detail for an AI agent or new contributor to understand and reproduce a feature without reading every source file. It covers both observable behaviors and the architectural and design reasoning behind them — organized around a feature, not around individual decision points (which distinguishes it from ADRs).

## Ownership

SPEC.md files are user-owned intent. Claude must never create or modify a SPEC.md without presenting the complete proposed content and receiving explicit user approval. This rule has no exceptions.

## File placement

SPEC.md lives at the root of the feature or subsystem directory it describes:

- `apps/sveltekit/board/SPEC.md` — kanban board UI
- `docker/api/SPEC.md` — API service
- `docker/localizer/SPEC.md` — localizer service
- `scripts/SPEC.md` — CLI scripts

One SPEC.md per deployable unit or distinct subsystem. Sub-specs (e.g. `docker/localizer/feature-extraction/SPEC.md`) are permitted when a subsystem has clearly distinct sub-features, but the default is one per top-level directory.

## File structure

```markdown
# {Feature Name}

## What it does
One paragraph. Plain-language summary of the feature's purpose and scope.
Not how it works — what it achieves for the user.

## Behaviors
Bulleted list of observable behaviors. Each bullet is a testable statement.
Grouped by sub-feature when the feature is large.

- When {trigger}, {outcome}.
- When {trigger}, {outcome}.

## Design decisions
Bulleted list of non-obvious choices and their rationale.

- {Decision} — {rationale}.
- {Decision} — {rationale}.

## Key files
Bulleted list of the most important files, with one-line descriptions.
Not exhaustive — just enough to orient a reader.

- `src/lib/components/Board.svelte` — main 5-column kanban layout
- `src/routes/api/tickets/[id]/+server.ts` — PATCH endpoint for status changes

## Constraints
Optional. Bulleted list of hard constraints: performance requirements,
compatibility, security, dependency restrictions. Omit if none are notable.
```

All sections are required except Constraints (include only when notable constraints exist).

## Writing guidelines

- **Behaviors are the core.** Each behavior should be independently testable. Use "When {trigger}, {outcome}" format consistently.
- **Visual behaviors are behaviors.** Hover states, transitions, focus treatment, active/pressed feedback, spacing rhythm, and animation are all observable, testable behaviors — not implementation details. "When a card is hovered, it lifts slightly and the border brightens with a smooth transition" belongs in the Behaviors section. A spec detailed enough to reproduce the feature's look and feel, not just its functionality, is the goal.
- **Design decisions capture the "why" that code cannot express.** If the rationale is obvious from the code, omit the decision.
- **Avoid implementation details in Behaviors.** "When a card is dragged to a new column, the status updates" is correct. "When `onfinalize` fires, the handler calls `fetch('/api/tickets/...')`" leaks implementation. The distinction: behaviors describe what a user observes; implementation details describe how the code achieves it. Specific CSS classes or function names are implementation details. Transition duration, hover effect, and focus ring appearance are observable behaviors.
- **Present tense throughout.** "Renders", "displays", not "should render", "will display".
- **Target 50–150 lines** for a typical subsystem. UI-heavy features with detailed visual behaviors may exceed this — that's fine. A spec that takes longer to maintain than the code it describes is too verbose, but a spec that omits visual behaviors to hit a line count is too terse.
- **No frontmatter.** Unlike tickets, specs have no YAML frontmatter. The filename and location provide all the metadata needed.
