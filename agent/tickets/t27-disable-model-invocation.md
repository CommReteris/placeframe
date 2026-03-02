---
id: T27
title: Add disable-model-invocation to side-effect skills
status: blocked
depends_on: []
---

# T27: Add disable-model-invocation to side-effect skills

## Goal

Add `disable-model-invocation: true` to allow-tool, tidy-commits, and debrief so they only fire on explicit `/skill` invocation, not auto-triggered by Claude.

## Context

These three skills have side effects (modifying settings.json, rewriting git history, writing to multiple repo locations) where timing should be user-controlled. The `disable-model-invocation` frontmatter field is the intended mechanism, but upstream Claude Code bug #26251 sometimes prevents even explicit slash-command invocation when the field is set. Blocked until that's resolved.

## Key files

- `.claude/skills/allow-tool/SKILL.md`
- `.claude/skills/tidy-commits/SKILL.md`
- `.claude/skills/debrief/SKILL.md`

## Done when

- Upstream bug #26251 is confirmed fixed
- All three skills have `disable-model-invocation: true` in frontmatter
- Verified that `/allow-tool`, `/tidy-commits`, and `/debrief` still work when explicitly invoked
