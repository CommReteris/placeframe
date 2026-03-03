---
id: T29
title: Add allowed-tools frontmatter to skills with narrow tool needs
status: blocked
depends_on: []
---

# T29: Add allowed-tools frontmatter to skills with narrow tool needs

## Goal

Declare `allowed-tools` in frontmatter for skills that only need a subset of tools, reducing their access surface.

## Context

Several skills use fewer tools than they have access to. allow-tool only needs Read and Edit. debrief only needs Read, Write, and Edit. Declaring `allowed-tools` would prevent accidental use of Bash or other tools during those skills. However, upstream enforcement of `allowed-tools` has had bugs (Claude Code issue #18837). Blocked until enforcement is reliable.

## Key files

- `.claude/skills/allow-tool/SKILL.md`
- `.claude/skills/debrief/SKILL.md`

## Done when

- Upstream issue #18837 is confirmed fixed
- allow-tool has `allowed-tools: [Read, Edit]` in frontmatter
- debrief has `allowed-tools: [Read, Write, Edit]` in frontmatter
- Verified both skills still function correctly with restricted tools
