---
name: debrief
description: Scan the conversation for uncaptured context before clearing. Surface decisions, insights, and loose threads that didn't land in a repo artifact. Use before /clear or ending a session.
disable-model-invocation: true
---

Review the current conversation for meaningful context that was not persisted to a repo artifact. Run this before clearing context to avoid losing insights.

## Step 1: Scan the conversation

Review the full conversation history. Look for:

- **Decisions about how the project works** — conventions, rules, preferences that should be in CLAUDE.md, a spec, or a skill
- **"We should do X later"** — ideas, improvements, or future work that should be a ticket
- **Design rationale** — the "why" behind a choice that should be in a spec or ticket detail file
- **Identified gaps or problems** — issues noticed but not yet tracked
- **User preferences** — workflow habits, tool preferences, communication style that should be in a memory file
- **Open threads** — discussions that started but didn't conclude, where the interim thinking is worth preserving

Ignore:
- Working-through-the-problem reasoning that led to an already-captured outcome
- Implementation details already reflected in committed code
- Anything already written to a file (ticket, spec, skill, CLAUDE.md, memory)

## Step 2: Report

If nothing is uncaptured: say so. "Nothing uncaptured — safe to clear."

If something is uncaptured: list each item in priority order (decisions about how the project works > identified gaps or problems > future work ideas > user preferences > open threads), with:
- What the insight/decision/thread is (one line)
- Where it should go (ticket, spec update, CLAUDE.md rule, memory file, skill tweak)

Do not write anything yet — present the list and let the user pick which items to capture.

## Step 3: Write

For each item the user approves:
- Write it to the appropriate location
- Offer to `/commit`

For items the user declines: drop them. If the user says "all of them," write them all.
