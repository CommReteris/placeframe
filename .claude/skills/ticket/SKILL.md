---
name: ticket
description: Pick up and work on a roadmap ticket.
---

Work on a ticket from the Placeframe roadmap. Follow these steps:

1. **Read the roadmap**: Read `agent/plans/roadmap.md` to see all tickets and their statuses.

2. **Select a ticket**: If the user specified a ticket (e.g., `/ticket T4`), use that one. Otherwise, present the available tickets (status is not `Done` or `Blocked`) and ask the user which to work on.

3. **Read the detail file**: Read the ticket's detail file from `agent/plans/`.

4. **Check status and act accordingly**:
   - **`Design needed`**: Present the open questions listed in the ticket. Discuss with the user until the approach is clear. Then update the status to `Plan needed` and proceed to the next step.
   - **`Plan needed`**: Enter plan mode. Read the ticket's detail file, explore the codebase, write an implementation plan, and get user approval. Update the detail file with the approved plan. Update the roadmap status to `Ready`.
   - **`Ready`**: Begin implementation. Follow the plan in the detail file.
   - **`Done`** or **`Blocked`**: Tell the user and ask what they'd like to do.

5. **Implement**: Work through the plan. After each logical chunk, verify against the "Done when" criteria in the detail file.

6. **Verify**: Run all "Verifiable now" checks from the "Done when" section. Report which passed and which failed. If any "Requires hardware/infra" items exist, list them as remaining manual verification.

7. **Update the roadmap**: Set the ticket's status to `Done` in `roadmap.md`. If the ticket spawned new work, create a new ticket file and add it to the roadmap.

8. **Commit**: Use `/commit` or `/tidy-commits` as appropriate.
