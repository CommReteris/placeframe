---
name: roadmap
description: Create, import, query, and reorganize tickets on the Placeframe roadmap. Use when the user wants to create a ticket, import tickets from a list, check ticket status, or restructure the roadmap.
argument-hint: "[create|import|query|reorganize]"
---

Manage the Placeframe roadmap tickets. Four workflows: create, import, query, reorganize.

Reference docs: `.claude/skills/shared/ticket-format.md` (frontmatter schema, statuses, epic convention).
Ticket files: `agent/tickets/**/t*.md` (recurses into epic subdirectories).

## Determine workflow

If the user's intent is clear, proceed directly. Otherwise ask which workflow they want:
- **Create** — add a single new ticket
- **Import** — bulk-create tickets from a list or braindump
- **Query** — filter and display tickets by status, dependency, or keyword
- **Reorganize** — change statuses, update dependencies, merge/split tickets

## 1. Create

1. Read all `agent/tickets/**/t*.md` files to find the highest ticket number.
2. Assign the next T-number (e.g., if T17 exists, the new ticket is T18).
3. Ask the user for: title, status (default `design-needed`), dependencies (default `[]`), and a brief goal.
4. **Check sizing.** Evaluate the proposed scope against the sizing heuristics in `ticket-format.md`. If the goal implies multiple unrelated actions (fails the one-sentence test), or the scope would likely exceed ~400 lines of change or touch many unrelated subsystems, propose a decomposition — suggest how to split and what the individual tickets would be. The user decides whether to split or keep as-is.
5. Ask which epic to place the ticket in (list existing epic directories, plus "root" for ungrouped). Default to root if the user doesn't specify.
6. Write `agent/tickets/{epic}/t{N}-{slug}.md` (or `agent/tickets/t{N}-{slug}.md` for root) with full ticket structure (frontmatter + Goal/Context/Approach/Done-when sections). Slug is derived from the title: lowercase, hyphens, no special characters.
7. Offer to `/commit`.

## 2. Import

1. Accept a list of items from the user — could be bullet points, numbered list, freeform text, or pasted from elsewhere.
2. Extract discrete ticket ideas. For each: derive a title, suggest a status (default `design-needed`), and identify dependencies on existing tickets.
3. **Check sizing.** Evaluate each proposed ticket against the sizing heuristics in `ticket-format.md`. Flag any that fail the one-sentence test or appear too large, and suggest splits. Also flag items that appear too small (no design decisions) and suggest grouping or dropping them.
4. Ask which epic to place the batch in (or root). All tickets in a single import go to the same epic by default, but the user can override per-ticket during review.
5. Present the parsed list for user review. Allow edits, deletions, and reordering.
6. After approval, create all ticket files (same process as Create, in sequence).
7. Offer to `/commit`.

## 3. Query

1. Read frontmatter from all `agent/tickets/**/t*.md` files.
2. Apply filters based on user request:
   - **By status**: e.g., "show me all ready tickets"
   - **By dependency**: e.g., "what depends on T5?"
   - **By keyword**: search title and body text
   - **By epic**: e.g., "show ci tickets" — filter by parent directory name
   - **Blocked**: show tickets whose `depends_on` includes incomplete tickets
3. Present results in a clean table or grouped list. Include id, title, status, epic (directory name or "root"), and dependencies.

## 4. Reorganize

Handle structural changes to the roadmap:
- **Change status**: Update the `status` field in the ticket's YAML frontmatter. Validate the transition makes sense.
- **Update dependencies**: Edit `depends_on` in frontmatter. Warn about circular dependencies.
- **Merge tickets**: Combine two tickets into one. Move content from the absorbed ticket into the survivor. Mark the absorbed ticket as done with a note.
- **Split ticket**: Break one ticket into multiple. Create new tickets and update the original.
- **Move to epic**: Move a ticket file from one directory to another (e.g., root to `ci/`, or `ci/` to `board/`). Use `git mv` to preserve history.
- **Create epic**: Create a new subdirectory under `agent/tickets/` with an optional `EPIC.md`.
- **Reorder/renumber**: Not supported (ticket IDs are permanent). Suggest using dependencies to express ordering instead.

After any changes, offer to `/commit`.
