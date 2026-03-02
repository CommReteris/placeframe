---
id: T36
title: Add fallback for ambiguous prose/code classification in commit
status: ready
depends_on: []
---

# T36: Add fallback for ambiguous prose/code classification in commit

## Goal

Add guidance for when a file doesn't clearly fit the prose or code classification.

## Context

The commit skill classifies files as prose (markdown, text, skill files) or code (Python, configs, .gitignore, pyproject.toml) and commits them separately. But some files are ambiguous — e.g., a `pyproject.toml` change that's just a dependency bump feels more like prose, and `.json` config files could go either way. Currently there's no fallback for ambiguous cases.

## Key files

- `.claude/skills/commit/SKILL.md` — step 3

## Approach

Add to step 3: "When a file doesn't clearly fit either category, ask the user."

## Done when

- Step 3 has a fallback clause for ambiguous file classification
