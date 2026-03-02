---
name: roadmap
description: Create, import, query, and reorganize tickets on the Placeframe roadmap.
---

Manage the Placeframe roadmap tickets. Four workflows: create, import, query, reorganize.

Reference docs: `.claude/skills/shared/ticket-format.md` (frontmatter schema, statuses).
Ticket files: `agent/tickets/t*.md`.

## Determine workflow

If the user's intent is clear, proceed directly. Otherwise ask which workflow they want:
- **Create** — add a single new ticket
- **Import** — bulk-create tickets from a list or braindump
- **Query** — filter and display tickets by status, dependency, or keyword
- **Reorganize** — change statuses, update dependencies, merge/split tickets

## 1. Create

1. Read all `agent/tickets/t*.md` files to find the highest ticket number.
2. Assign the next T-number (e.g., if T17 exists, the new ticket is T18).
3. Ask the user for: title, status (default `design-needed`), dependencies (default `[]`), and a brief goal.
4. Write `agent/tickets/t{N}-{slug}.md` with full ticket structure (frontmatter + Goal/Context/Approach/Done-when sections). Slug is derived from the title: lowercase, hyphens, no special characters.
5. Offer to `/commit`.

## 2. Import

1. Accept a list of items from the user — could be bullet points, numbered list, freeform text, or pasted from elsewhere.
2. Extract discrete ticket ideas. For each: derive a title, suggest a status (default `design-needed`), and identify dependencies on existing tickets.
3. Present the parsed list for user review. Allow edits, deletions, and reordering.
4. After approval, create all ticket files (same process as Create step 4, in sequence).
5. Offer to `/commit`.

## 3. Query

1. Read frontmatter from all `agent/tickets/t*.md` files.
2. Apply filters based on user request:
   - **By status**: e.g., "show me all ready tickets"
   - **By dependency**: e.g., "what depends on T5?"
   - **By keyword**: search title and body text
   - **Blocked**: show tickets whose `depends_on` includes incomplete tickets
3. Present results in a clean table or grouped list. Include id, title, status, and dependencies.

## 4. Reorganize

Handle structural changes to the roadmap:
- **Change status**: Update the `status` field in the ticket's YAML frontmatter. Validate the transition makes sense.
- **Update dependencies**: Edit `depends_on` in frontmatter. Warn about circular dependencies.
- **Merge tickets**: Combine two tickets into one. Move content from the absorbed ticket into the survivor. Mark the absorbed ticket as done with a note.
- **Split ticket**: Break one ticket into multiple. Create new tickets and update the original.
- **Reorder/renumber**: Not supported (ticket IDs are permanent). Suggest using dependencies to express ordering instead.

After any changes, offer to `/commit`.
