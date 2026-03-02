---
id: T44
title: Add before/after examples to commit-style.md
status: done
depends_on: []
---

# T44: Add before/after examples to commit-style.md

## Goal

Add concrete examples of good and bad commit messages to the commit style guide.

## Context

Examples are the strongest steering signal for LLMs. The commit style guide has clear rules but no examples.

The main risk of adding examples to skill prose is **overfitting** — Claude pattern-matches too closely to the specific example rather than generalizing from the rules. But commit messages are the right task for examples precisely because they're formulaic. You *want* consistency, not creativity. Overfitting to a good commit message example is effectively the desired outcome. This is unlike tasks with high variance (spec behaviors, ticket descriptions) where anchoring to a specific example would be harmful.

The file is currently 10 lines. Adding 5-10 lines of examples keeps it well within the recommended skill content budget.

## Key files

- `.claude/skills/shared/commit-style.md`

## Approach

Add 2-3 before/after pairs showing a bad message and the corrected version. Cover the most common mistakes: vague subjects, missing prefix, mixing prose and code, over-explaining in the body.

## Done when

- commit-style.md has concrete before/after examples
- Examples demonstrate the rules already documented, not new rules
