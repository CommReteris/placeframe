---
id: T52
title: Plan mode exit UX breaks multi-step skill workflows
status: blocked
depends_on: []
---

# T52: Plan mode exit UX breaks multi-step skill workflows

## Goal

Find or create a reliable way to exit plan mode during `/workon` without losing the skill's lifecycle context.

## Context

When `/workon` enters plan mode (step 3a), the plan gets written and `ExitPlanMode` is called. Claude Code then presents 4 hardcoded exit options:

1. **Yes, clear context and auto-accept edits** (shift+tab) — the default
2. **Yes, auto-accept edits** — preserves context
3. **Yes, manually approve edits**
4. **Type here to tell Claude what to change**

The default (#1) clears conversation context, which destroys the `/workon` skill's state. The session restarts with a raw "Implement the following plan:" message — no awareness that it was inside a `/workon` flow. Result: implementation happens without the ticket lifecycle (no status update to `in-review`, no `## Log` section, no verification step).

Option #2 works correctly — context is preserved and `/workon` continues through implementation. But there's no way to change the default, and no option to just drop back to the REPL without starting anything.

These options are not configurable via `settings.json`, `CLAUDE.md`, hooks, or any other mechanism as of March 2026.

### Upstream issues

- [anthropics/claude-code#18599](https://github.com/anthropics/claude-code/issues/18599) — request to change the default exit option
- [anthropics/claude-code#26930](https://github.com/anthropics/claude-code/issues/26930) — exit options not discoverable when ExitPlanMode is rejected

### Current workaround

Pick option #2 ("Yes, auto-accept edits") instead of the default when exiting plan mode during `/workon`. This preserves context and the skill continues autonomously.

## Done when

- Plan mode exit does not break `/workon` lifecycle, either via:
  - Anthropic fixing the UX (configurable default, "return to REPL" option)
  - A hook-based workaround that re-injects `/workon T{N}` after context clear
  - A skill redesign that's resilient to context loss
