# T59 Plan: Add convention audit step to /workon workflow

## Context

LLM-generated code reliably violates project conventions that conflict with training priors (inline aggressively, no decorative comments, full-word variable names, etc.). A post-generation self-correction step in `/workon` is more reliable than relying on generation-time instruction compliance.

## Approach

### 1. Create `.claude/skills/shared/audit-conventions.md`

New shared reference doc listing counter-training conventions. Each entry has:
- Convention statement (what the rule is)
- Detection guidance (what violations look like)
- Before/after example
- Whether it's mechanical (auto-fix) or judgment (flag only)

Conventions to cover:
1. **Inline aggressively** — single-use variables/functions. *Judgment* — flag only.
2. **No decorative comments** — `# ---` dividers, decorative formatting, gratuitous docstrings. *Mechanical* — auto-fix.
3. **Full-word variable names** — `res` → `result`, `cmd` → `command`. *Mechanical* — auto-fix.
4. **No unnecessary abstractions** — helper functions for one-time operations, premature extraction. *Judgment* — flag only.
5. **Relative imports** — `from package.module` → `from .module` for intra-package. *Mechanical* — auto-fix.
6. **Use run_command/check_command** — not raw `subprocess.run`; `check_command` for expected failures, not try/except. *Mechanical* — auto-fix.

Target: ~60-80 lines. Under 100, so no ToC needed per skill-authoring.md.

### 2. Add audit step to `.claude/skills/workon/SKILL.md`

Insert new step 5 ("Audit conventions") between current step 4 (TDD implementation) and current step 5 (Verify). Renumber steps 5→6, 6→7, 7→8, 8→9, 9→10.

The step instructs:
- Read `.claude/skills/shared/audit-conventions.md`
- Run `git diff main...HEAD --name-only` to find changed code files (filter out prose/markdown)
- For each changed file, run `git diff main...HEAD -- <file>` to see only the branch's changes
- Review changed lines against conventions. Only flag/fix violations in lines the branch introduced or modified.
- Mechanical violations: fix in place
- Judgment violations: flag with a brief comment for the user to see at commit review
- Pre-existing violations noticed in surrounding code: record in the ticket's `## Observations` section
- Skip this step entirely for prose-only tickets

### 3. Add `## Observations` to `.claude/skills/shared/ticket-format.md`

Add to the Body structure section, after the `## Log` entry. Required section once implementation begins (like Log). Records pre-existing issues noticed in surrounding code during implementation. States "No pre-existing issues noticed." when there's nothing to report.

### 4. Update workon's submit step

The submit step (currently 8, will become 9) already writes the `## Log` section. Update it to also write the `## Observations` section.

## Key files

- `.claude/skills/shared/audit-conventions.md` — **create** — criteria doc with 6 conventions
- `.claude/skills/workon/SKILL.md` — **modify** — insert step 5, renumber 5-9 → 6-10, update submit step
- `.claude/skills/shared/ticket-format.md` — **modify** — add Observations to body structure

## Verification

- Read the final workon SKILL.md and verify step numbering is sequential 1-10
- Read audit-conventions.md and verify all 6 conventions have detection guidance + before/after examples + mechanical/judgment classification
- Read ticket-format.md and verify Observations section is documented
- Verify all cross-references between files are correct (workon references audit-conventions.md, ticket-format.md documents Observations)
