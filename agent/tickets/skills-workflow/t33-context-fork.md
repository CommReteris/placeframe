---
id: T33
title: Add context:fork to read-heavy skill phases
status: blocked
depends_on: []
---

# T33: Add context:fork to read-heavy skill phases

## Goal

Use `context: fork` for read-heavy exploration phases in skills to preserve main conversation context.

## Context

Several skills have phases that consume significant context with file reads but don't need main-thread interaction: backfill-spec step 1 (code exploration), workon step 3b (warm-up from plan). Running these in a forked subagent would keep the main conversation clean. However, `context: fork` is buggy upstream — multiple open issues report inconsistent failures (#17283, #18394) and incompatibility with AskUserQuestion (#19751). Blocked until upstream stabilizes.

## Key files

- `.claude/skills/backfill-spec/SKILL.md` — step 1
- `.claude/skills/workon/SKILL.md` — step 3b

## Done when

- Upstream context:fork bugs are confirmed fixed
- backfill-spec step 1 runs in a fork with `agent: Explore`
- workon step 3b runs in a fork with `agent: Explore`
- Verified both skills still function correctly (file reads work, results return to main thread)
