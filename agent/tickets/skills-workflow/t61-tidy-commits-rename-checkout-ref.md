---
id: T61
title: Add rename and checkout_ref fields to tidy-commits wrapper
status: in-review
depends_on: []
plan: t61-plan.md
---

# T61: Add rename and checkout_ref fields to tidy-commits wrapper

## Goal

Reduce plan complexity and token cost for reorg-heavy branches by adding two new fields to the tidy-commits JSON schema.

## Context

During a roadmap consolidation (16 file renames + 2 partial file splits), the tidy-commits plan ballooned because the current schema lacks primitives for two common operations:

1. **Renames** require a `checkout` (new path) + `delete` (old path) pair per file. A 16-file reorg produces 32 entries when one mapping would suffice.
2. **Intermediate file states** require embedding the full file content as a JSON string in the `content` field. For a ~150-line reference doc, this forced a Python detour just to escape the content safely. Checking out from the original commit that produced that intermediate state would avoid embedding entirely.

The wrapper (`tidy_commits_wrapper.py`) processes file operations in `execute_plan` (lines 74-83): `checkout` does `git checkout <backup> -- <files>`, `delete` does `git rm`, and `content` writes literal strings to disk then `git add`s them. The `Commit` Pydantic model (lines 19-30) validates that at least one operation exists. Both new fields slot into this same loop.

The skill prompt (`SKILL.md`) documents the JSON schema in two places: the "JSON schema" code block (lines 35-48) and the "Field reference" section (lines 51-58). It also has rename-specific guidance in "Important rules" (line 77) that currently says to use `delete` for the old-path side of renames. All three locations need updating to document the new fields and state when to prefer them over the existing patterns. This is critical — if the skill prompt doesn't teach the LLM to use `rename` over `checkout`+`delete`, the fields won't get used.

The commit hashes used in `checkout_ref` come from the analysis phase (step 2), where the LLM runs `git log --oneline <base>..HEAD` and `git show` to inspect individual commits. The LLM already has these hashes in context when it writes the plan.

## Key files

- `scripts/src/scripts/tidy_commits_wrapper.py` — `execute_plan` loop (lines 74-83), `Commit` model (lines 19-30)
- `.claude/skills/tidy-commits/SKILL.md` — JSON schema block (lines 35-48), field reference (lines 51-58), rename rule (line 77)

## Approach

**Wrapper changes** (`tidy_commits_wrapper.py`):
- Add `rename: dict[str, str]` and `checkout_ref: dict[str, list[str]]` to the `Commit` model with empty defaults. Update the `has_file_operations` validator to accept them.
- `rename` implicitly checks out the old path from backup before `git mv` (the source file doesn't exist on the temp branch otherwise). This makes it fully self-contained — one field replaces `checkout`+`delete` pairs.
- `checkout_ref` uses `git checkout <ref> -- <path>` (auto-stages, handles binaries), not `git show`. Matches the existing `checkout` pattern.
- Operation ordering in `execute_plan`: `checkout` → `checkout_ref` → `rename` → `delete` → `content`. Rename after checkout allows combining both in one commit; `checkout_ref` alongside `checkout` since they're semantically similar.

**Skill prompt changes** (`SKILL.md`):
- Add `rename` and `checkout_ref` to the JSON schema example.
- Add field reference entries explaining when to use each: `rename` for pure renames (same content, different path), `checkout_ref` for intermediate file states where the desired version exists in a prior commit on the branch.
- Update the "Important rules" rename guidance to say "prefer `rename` field; fall back to `checkout`+`delete` only when the rename also involves content changes."
- In step 5 (partial file splits), add `checkout_ref` as the preferred approach when the intermediate state exists in a prior commit, with `content` as fallback for states that don't correspond to any single commit.

## Done when

- Wrapper handles `rename` field via `git mv`, auto-staged
- Wrapper handles `checkout_ref` field via `git checkout` from arbitrary refs
- Skill prompt documents both fields with preference guidance in schema, field reference, and rules sections
- Existing `checkout`, `delete`, and `content` fields continue to work unchanged

## Log

Clean implementation, no issues.

## Observations

No pre-existing issues noticed.
