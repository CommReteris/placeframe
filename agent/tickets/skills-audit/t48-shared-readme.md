---
id: T48
title: Add README index to .claude/skills/shared/
status: done
depends_on: []
---

# T48: Add README index to .claude/skills/shared/

## Goal

Add a brief README listing each shared reference file and what it covers, so new shared files are discoverable.

## Context

Skills reference shared files by path (e.g., `.claude/skills/shared/commit-style.md`). There's no index listing what's available. At current scale (4 files) this is manageable, but as shared references grow, an index prevents skills from duplicating content that already exists in a shared file they didn't know about.

## Key files

- `.claude/skills/shared/` — new file: `README.md`

## Done when

- README.md in shared/ lists each file with a one-line description
