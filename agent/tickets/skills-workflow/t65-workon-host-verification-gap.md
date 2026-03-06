---
id: T65
title: Audit workon skill for host-side verification gap
status: design-needed
depends_on: []
---

# T65: Audit workon skill for host-side verification gap

## Goal

Address the gap where the workon skill moves a ticket to `in-review` based on container-side checks, but the ticket's real acceptance criteria require host-side verification that the skill cannot perform.

## Context

T62 (Unity headless builds) was moved to `in-review` by the workon skill after passing all verification steps (ruff, basedpyright, pytest). But the actual acceptance criterion — "image builds successfully with `uv run setup-agent-sandbox --rebuild`" — can only be verified on the host, outside the agent container. Two bugs were found when the user ran the build on the host, meaning the ticket wasn't actually done.

The workon skill's step 6 (Verify) runs a fixed set of checks and any ticket-specific "Verifiable now" items. Step 9 (Submit for review) then auto-transitions to `in-review`. The ticket format already distinguishes "Verifiable now" from "Requires manual verification" in Done-when, but the skill doesn't gate the transition on the manual items — it just lists them.

The question is whether the skill should behave differently when manual verification items exist. Options:
- **Surface prominently**: keep auto-transitioning but make the "requires manual verification" items impossible to miss in the handoff message.
- **Block transition**: don't move to `in-review` when manual verification items exist; instead move to a state like `needs-host-verification` or keep at `ready` with a note.
- **No change**: the current behavior is fine — the user just needs to remember to verify before accepting. The Log section captures what happened.

## Key files

- `.claude/skills/workon/SKILL.md` — steps 6 and 9 are the relevant sections
- `.claude/skills/shared/ticket-format.md` — defines Done-when structure and status values

## Approach

Design needed — decide whether this is a skill change, a convention change, or acceptable as-is.

## Done when

- Decision is made and documented on how to handle tickets with host-side verification requirements
- If a skill change is chosen, workon SKILL.md is updated accordingly
