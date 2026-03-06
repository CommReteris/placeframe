# T61: Add rename and checkout_ref fields to tidy-commits wrapper

## Context

Complex branch reorgs (many file renames, partial file splits) produce bloated tidy-commits plans because the schema lacks primitives for two common operations. A 16-file rename currently requires 32 plan entries. Adding `rename` and `checkout_ref` fields cuts plan size and token cost significantly.

## Approach

### 1. Add fields to the `Commit` Pydantic model

In `scripts/src/scripts/tidy_commits_wrapper.py`, add two new fields to `Commit` (lines 19-30):

```python
rename: dict[str, str] = {}       # old_path -> new_path
checkout_ref: dict[str, list[str]] = {}  # ref -> [paths]
```

Update the `has_file_operations` validator to accept `rename` and `checkout_ref` as valid operations (line 28).

### 2. Add processing to `execute_plan`

In the commit-building loop (lines 74-83), add two new blocks between existing operations. Final ordering:

1. `checkout` (existing — lines 74-75)
2. `checkout_ref` — for each ref/paths pair: `git checkout <ref> -- <paths>` (auto-stages)
3. `rename` — for each old/new pair: `git checkout <backup> -- <old_path>`, then `mkdir -p` parent of new path, then `git mv <old_path> <new_path>`
4. `delete` (existing — lines 77-78)
5. `content` (existing — lines 80-83)

Implementation details:
- `checkout_ref` uses list-form `run_command(["git", "checkout", ref, "--"] + paths)` — same pattern as existing `checkout` on line 75
- `rename` must checkout from `backup` first (file doesn't exist on temp branch), then `git mv`. Use `Path.parent.mkdir(parents=True, exist_ok=True)` on the new path before `git mv` to handle directory creation.

### 3. Update SKILL.md

In `.claude/skills/tidy-commits/SKILL.md`, three locations need updating:

**JSON schema example** (lines 36-48): Add `rename` and `checkout_ref` fields to the example commit object.

**Field reference** (lines 51-58): Add entries for:
- `rename`: Dict of old path → new path. Use for pure renames (same content, different path). Implicitly checks out old path from backup. Prefer over `checkout`+`delete` pairs.
- `checkout_ref`: Dict of commit ref → list of file paths. Use for intermediate file states where the desired version exists in a prior commit on the branch. Prefer over `content` when the file state matches a known commit.

**Important rules — rename guidance** (line 77): Replace current guidance ("use `delete` for the old-path side of renames") with: "Prefer `rename` field for pure renames; fall back to `checkout`+`delete` only when the rename also involves content changes."

**Step 5 — partial file splits** (lines 62-66): Add `checkout_ref` as the preferred approach when the intermediate state exists in a prior commit, with `content` as fallback for states that don't correspond to any single commit.

### 4. Create tests

New file: `scripts/tests/test_tidy_commits_wrapper.py`

Tests will mock `common.run_command.run_command` and `common.run_command.check_command` at the system boundary, and exercise `execute_plan` directly. Key test cases:

- `rename` field calls `git checkout <backup> -- <old_path>` then `git mv <old_path> <new_path>` with parent dirs created
- `checkout_ref` field calls `git checkout <ref> -- <paths>` for each ref
- Multiple renames in one commit all execute
- Multiple refs in one `checkout_ref` each get their own checkout call
- Validator accepts commits with only `rename` (no checkout/delete/content)
- Validator accepts commits with only `checkout_ref`
- Existing fields (`checkout`, `delete`, `content`) continue to work unchanged
- Operation ordering: checkout before checkout_ref before rename before delete before content

## Key files

- `scripts/src/scripts/tidy_commits_wrapper.py` — add fields to Commit model, add processing to execute_plan
- `.claude/skills/tidy-commits/SKILL.md` — document new fields in schema, field reference, and rules
- `scripts/tests/test_tidy_commits_wrapper.py` — new test file

## Verification

- `uv run pytest scripts/tests/test_tidy_commits_wrapper.py` — all tests pass
- `uv run ruff check scripts/src/scripts/tidy_commits_wrapper.py scripts/tests/test_tidy_commits_wrapper.py`
- `uv run ruff format --check scripts/src/scripts/tidy_commits_wrapper.py scripts/tests/test_tidy_commits_wrapper.py`
- `uv run basedpyright scripts/src/scripts/tidy_commits_wrapper.py scripts/tests/test_tidy_commits_wrapper.py`
- Manual: read SKILL.md and confirm schema example, field reference, and rules are consistent
