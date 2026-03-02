# Skills Audit

Comprehensive review of all skills in `.claude/skills/`. Covers individual skill quality, cross-cutting concerns, alignment with upstream best practices (Anthropic docs, community patterns), and recommendations.

Audited: 2026-03-02

## Summary

The skill suite is unusually well-designed. The permission strategy (one gate per skill), prose/code commit separation, TDD enforcement with human review gates, and user-owned spec convention are all ahead of what the community typically does. The issues found are mostly about missing frontmatter features, a few edge cases in skill logic, and opportunities to harden security using newer Claude Code capabilities. The tidy-commits shell injection risk identified during audit has been resolved by landing the JSON plan + Pydantic executor that was previously stranded on a backup branch.

Severity labels: **high** = could cause incorrect behavior or data loss; **medium** = missed opportunity or friction; **low** = cosmetic or minor improvement.

---

## Per-Skill Findings

### 1. allow-tool

**What it does well:**
- Threat model is explicit and well-reasoned ("zero trust of Claude's output")
- Classification of read-only vs pre-approved vs unapproved writes is clear and exhaustive
- Generalization instruction ("if `git log --oneline -10` was prompted, propose `Bash(git log *)`") prevents overly narrow rules

**Issues:**

- **[medium] Missing `disable-model-invocation: true`.** This skill modifies `.claude/settings.json` — a security-sensitive file. If Claude decides to auto-invoke it based on the description matching some user utterance, it could propose permission changes the user didn't ask for. Add `disable-model-invocation: true` so it only fires on explicit `/allow-tool`.

- **[low] Classification list will go stale.** The read-only/pre-approved/unapproved lists are hardcoded. As the project adds new tools (e.g., `pnpm` for the SvelteKit app, `npx` for tooling), someone needs to remember to update this skill. Consider adding a note: "If the command doesn't fit any category, ask the user."

- **[low] No `allowed-tools` restriction.** This skill only needs Read and Edit. Adding `allowed-tools: [Read, Edit]` in frontmatter would prevent it from accidentally running Bash commands. (Note: enforcement of `allowed-tools` has had bugs — track upstream issue #18837 — but it's still worth declaring intent.)

### 2. backfill-spec

**What it does well:**
- The ownership model exception is explicitly justified and well-bounded
- Q&A batch process is a genuine innovation — avoids the "wall of unrenderable markdown" problem
- Gap-to-ticket pipeline ensures nothing falls through the cracks
- Sub-spec consideration for large subsystems shows good architectural thinking

**Issues:**

- **[medium] No guidance on conflicting information sources.** Step 1 says "the code is the source of truth for behavior, and the user is the source of truth for intent." But what happens when the code contradicts a ticket? Or when the user's stated intent contradicts what the code does? Add explicit conflict resolution: e.g., "If code and ticket disagree, note the discrepancy and ask the user which is correct."

- **[medium] No handling for partially-specced directories.** What if a SPEC.md already exists but is incomplete (e.g., someone started one manually)? The skill assumes "no spec exists." Add a check: if SPEC.md exists, read it, assess completeness, and either augment or start fresh (with user input).

- **[low] Step 6 ticket creation could clash with roadmap skill.** backfill-spec creates tickets directly. If the roadmap skill has recently been used and the user has a mental model of ticket numbering, creating tickets outside `/roadmap` could surprise them. Consider noting: "Uses the same numbering convention as `/roadmap create`."

- **[low] `context: fork` could help.** The Step 1 code exploration can consume significant context. Running the initial read phase in a fork subagent would protect the main conversation window. Not critical since the Q&A requires main-thread interaction, but worth considering for Step 1 specifically.

### 3. commit

**What it does well:**
- Reading the style guide every time (step 1) prevents drift from conventions
- Prose/code separation is enforced at the commit level
- Explicit heredoc format for commit messages avoids shell quoting issues
- "Never use `git add .` or `git add -A`" prevents accidental inclusion of sensitive files

**Issues:**

- **[medium] No dirty-tree guard.** The skill doesn't check for merge conflicts, rebase state, or other unusual git states before starting. If the repo is in the middle of a rebase or merge, `git commit` will behave unexpectedly. Add step 0: "Check `git status` for merge/rebase state. If the repo is in an unusual state, inform the user and abort."

- **[medium] No handling for empty diffs.** If the user runs `/commit` with no changes, the skill will run through all 7 steps before failing at `git commit`. Add an early exit: "If `git status` shows nothing to commit, say so and stop."

- **[low] Step 3 classification heuristic may misclassify.** `.toml`, `.json`, `.yaml` config files are classified as "code" but some are closer to prose (e.g., `pyproject.toml` dependency bumps vs actual code changes). The classification is documented but the edge cases could use a note: "When in doubt about classification, ask the user."

### 4. debrief

**What it does well:**
- The "ignore" list (already-captured outcomes, committed code, existing files) prevents duplication
- Routing items to the right destination (ticket vs spec vs CLAUDE.md vs memory) is explicit
- "If nothing uncaptured, say so" prevents unnecessary ceremony

**Issues:**

- **[medium] No scan of tool/skill changes.** The debrief scans for "decisions, insights, loose threads" but doesn't explicitly check whether any skills or shared references were updated during the session. If a skill was modified but not committed, that's a critical loose thread. Add: "Check if any `.claude/skills/` files were modified but not committed."

- **[low] No priority guidance.** When there are many uncaptured items, the user has to evaluate each one. Consider adding a suggested priority order: decisions > identified gaps > future work > preferences > open threads.

- **[low] Could benefit from `disable-model-invocation: true`.** Debrief is a session-lifecycle operation that should be user-initiated (before `/clear`). Auto-invocation would be disruptive mid-session.

### 5. roadmap

**What it does well:**
- Four distinct workflows with clear entry criteria
- Import workflow handles freeform braindump input gracefully
- Reorganize workflow explicitly warns about circular dependencies
- Permanent ticket IDs (no renumbering) is a good design choice

**Issues:**

- **[medium] No validation of `depends_on` references.** When creating or importing tickets, the skill doesn't verify that referenced ticket IDs in `depends_on` actually exist. A typo like `depends_on: [T99]` when T99 doesn't exist would create a silently broken dependency. Add: "Verify all `depends_on` references resolve to existing tickets."

- **[medium] Query workflow doesn't use `tickets.py`.** Step 3.1 says "Load all tickets using `load_tickets()` pattern (read frontmatter from all files)." But "pattern" is ambiguous — does it mean call the Python function or replicate its logic manually? Clarify: either "Run `load_tickets()` via a script" or "Read and parse frontmatter directly" (and explain why not using the function).

- **[low] Import workflow has no duplicate detection.** If the user imports a braindump that includes ideas already tracked as tickets, the skill will create duplicates. Add: "Check imported items against existing ticket titles for potential duplicates."

- **[low] No `argument-hint` in frontmatter.** Adding `argument-hint: [create|import|query|reorganize]` would improve autocomplete UX.

### 6. tidy-commits

**What it does well:**
- The wrapper/plan separation is excellent — deterministic safety (backup, invariance check, rollback) is separate from LLM-generated logic
- JSON plan + Pydantic executor eliminates shell injection entirely (commit messages are passed as Python strings to `run_command`, never interpolated into shell)
- Pydantic validation catches malformed plans before any git operations begin
- `content` field enables partial file splits that were previously unsupported
- "Never use `git rebase -i`" shows awareness of interactive-input limitation
- File rename handling guidance via `delete` field is a subtle but important edge case

**Issues:**

- **[medium] Uncommitted-changes check is buried.** The "Important rules" section says "If there are uncommitted changes, ask the user to commit or stash them first." But this is at the end, not in the main flow. By step 4 (writing the plan), the skill has already invested significant work. Move this check to step 0, before any analysis.

- **[medium] No `disable-model-invocation: true`.** This skill rewrites git history. It should never auto-trigger — only on explicit `/tidy-commits`. Add the frontmatter field.

- **[low] Author preservation logic is complex.** The instruction "use the author from the earliest one (or the most common one if they differ)" gives the LLM two options without a clear tiebreaker. Simplify to one rule: "Use the author from the earliest original commit."

### 7. workon

**What it does well:**
- Full lifecycle coverage from ticket selection through spec maintenance
- TDD enforcement with explicit human review gate after RED phase is best-in-class
- Spec drift detection (step 6a) with explicit "never auto-correct" rule prevents silent spec corruption
- Warm-up phase (3b) for resuming work across sessions is a genuine innovation
- Checking SPEC.md for regression tests before implementing is excellent

**Issues:**

- **[medium] RED phase "context pollution" risk.** Research on AI+TDD shows that when the same LLM context writes both tests and implementation, it tends to write tests that validate anticipated code rather than requirements. The skill mitigates this with the human review gate, but doesn't address the underlying risk. Consider adding: "When writing tests in the RED phase, focus exclusively on the 'Done when' criteria and spec behaviors. Do not consider implementation approach — the tests should encode requirements, not predicted code structure."

- **[medium] No timeout or scope limit on the implementation cycle.** A complex ticket could lead to an unbounded RED-GREEN-REFACTOR loop. Add guidance: "If the RED phase produces more than ~10 test cases, discuss scope with the user before proceeding. Large test suites suggest the ticket should be split."

- **[medium] Step 5 verification is Python-only.** The verify step runs `ruff`, `basedpyright`, and `pytest` — all Python tools. But tickets could involve SvelteKit/TypeScript code (the board). Add: "For TypeScript changes, also run `pnpm check` and `pnpm lint` from the relevant app directory. Refer to CLAUDE.md Web Conventions section."

- **[low] No `argument-hint` in frontmatter.** Adding `argument-hint: [ticket-id]` would hint that `/workon T4` is valid syntax.

- **[low] Step 8 says "Offer to `/commit` or `/tidy-commits` as appropriate" but doesn't define when each is appropriate.** Add: "Use `/commit` for single logical changes. Use `/tidy-commits` when the implementation accumulated multiple WIP commits that should be reorganized for review."

---

## Shared Reference Files

### commit-style.md

- **[low] No examples.** A before/after example of a good vs bad commit message would make the guide more concrete. The rules are clear but examples accelerate learning.

### spec-format.md

- **[low] Constraint section guidance is thin.** "Include only when notable constraints exist" doesn't help decide what's "notable." Add: "Examples of notable constraints: performance SLAs, browser compatibility requirements, API backward-compatibility guarantees, dependency version pins."

### testing.md

- **Solid.** No significant issues found. The AAA pattern guidance, factory-over-fixture preference, and mock-only-at-boundaries rules align with industry best practices.

- **[low] No mention of TypeScript/Vitest.** The testing guide is Python-only, but the project has a SvelteKit app using Vitest. Either add a TypeScript section or note that web testing conventions are in CLAUDE.md.

### ticket-format.md

- **[low] No guidance on ticket size.** When is a ticket too large and should be split? When is it too small? Add: "A ticket should represent a single shippable unit of work. If 'Done when' has more than ~7 criteria, consider splitting."

---

## Cross-Cutting Concerns

### A. Missing frontmatter features

Several skills don't use available frontmatter fields that would improve safety and UX:

| Skill | `disable-model-invocation` | `allowed-tools` | `argument-hint` |
|---|---|---|---|
| allow-tool | should add | should add (`Read, Edit`) | n/a |
| backfill-spec | no (needs interaction) | no (needs many tools) | `[directory-path]` |
| commit | no (intentionally auto-triggerable per CLAUDE.md "offer to commit") | no (needs Bash for git) | `[hint-text]` |
| debrief | should add | no (needs Read/Write/Edit) | n/a |
| roadmap | no (user asks for it) | no (needs many tools) | `[create\|import\|query\|reorganize]` |
| tidy-commits | **should add** | no (needs Bash for git) | n/a |
| workon | no (user asks for it) | no (needs everything) | `[ticket-id]` |

### B. No skill uses `context: fork`

None of the 7 skills use isolated subagent context. For some (commit, allow-tool) this is correct — they need main-thread interaction. But backfill-spec's code exploration phase and workon's warm-up phase (3b) are read-only context-building that could run in a fork to preserve the main conversation window. This becomes more valuable as conversations grow long.

### C. Inconsistent "offer to commit" phrasing

- CLAUDE.md says: 'offer to commit by saying "Want me to `/commit` this?"'
- backfill-spec says: "Offer to `/commit`"
- roadmap says: "Offer to `/commit`."
- workon says: "Offer to `/commit` or `/tidy-commits`"
- tidy-commits doesn't offer (it's a commit-adjacent skill itself)

The phrasing is close enough to not cause problems, but standardizing to the CLAUDE.md phrasing ("Want me to `/commit` this?") would be more consistent.

### D. Shared references are not discoverable from skills

Skills reference shared files by path (`.claude/skills/shared/commit-style.md`), which works. But there's no index or manifest listing all shared references. If someone adds a new shared file, existing skills won't know about it. This is fine at current scale (4 shared files) but could become a maintenance issue. Consider a brief README in `shared/` listing what each file covers.

### E. Permission rules in settings.json

The current permission allowlist is well-curated but has a few observations:

- **`Bash(cat *)` and `Bash(tail *)` are allowed** — these duplicate the Read tool's functionality. Per CLAUDE.md, Read should be preferred. The permissions aren't wrong (they don't create risk), but they may encourage Claude to use Bash for file reading instead of the dedicated tool.

- **`Bash(find *)` is allowed** — this duplicates Glob. Same observation.

- **`Bash(source *)` is allowed** — this could source arbitrary shell scripts. In the zero-trust threat model described by allow-tool, sourcing a file executes whatever it contains. This is probably fine in the FOSS/no-secrets context, but it's the most permissive rule on the list.

- **No `Skill(*)` permission rule.** Skills currently require user approval to invoke. If specific skills should auto-trigger (like `/commit` per CLAUDE.md's "offer to commit" instruction), adding `Skill(commit)` to the allow list would remove that friction.

### F. No skill versioning or changelog

When a skill is modified, there's no record of what changed or why. Skills are committed alongside other prose, but there's no convention for noting significant skill behavior changes. For a project that values decision tracking (specs, tickets, plans), this is a gap. Consider: either a brief changelog comment at the top of SKILL.md files, or treating significant skill changes as ticket-worthy work.

---

## Architectural Observations

### Strengths

1. **Permission model is principled.** "One gate per skill" is a cleaner model than most projects achieve. The threat model is explicit and well-reasoned.

2. **Prose/code separation is enforced at multiple levels.** Commit style guide, commit skill, and tidy-commits all enforce it. This is unusually rigorous.

3. **The spec/ticket/plan trilogy is well-designed.** Each captures different concerns (durable record / transient intent / strategic decisions). The lifecycle flow between them is clear.

4. **TDD with human gates is the right call.** Research shows AI+TDD without human review produces tests that validate implementation rather than requirements. The explicit RED-phase review gate addresses this directly.

5. **The tidy-commits wrapper pattern is novel and safe.** Separating deterministic safety (backup/invariance/rollback) from LLM-generated logic is a design pattern worth publicizing.

### Potential improvements

1. **Consider a `context: fork` + `agent: Explore` pattern for read-heavy skill phases.** The warm-up phase in workon (3b) and the code reading phase in backfill-spec (step 1) are read-only exploration that could run in a fork to preserve context.

2. **Consider a shared "pre-flight check" pattern.** Multiple skills need to verify git state before starting (clean tree, not in rebase, etc.). This could be a shared reference file (`.claude/skills/shared/git-preflight.md`) that skills reference, avoiding duplication.

3. ~~**The `tickets.py` module could do more.**~~ **Resolved** — `tickets.py` was dead code (a reference implementation Claude read but never executed). Deleted; skill references simplified to direct instructions.

4. **Testing conventions should cover TypeScript.** The project has a SvelteKit app with Vitest tests. The testing.md shared reference only covers Python/pytest. Either extend it or create a separate `testing-web.md`.

---

## Recommendations (prioritized)

### Do now (high-value, low-effort)

1. Add `disable-model-invocation: true` to tidy-commits and allow-tool
2. Move tidy-commits' uncommitted-changes check to step 0
3. ~~Add shell-injection mitigation note to tidy-commits script generation instructions~~ **Resolved** — JSON plan + Pydantic executor eliminates shell injection entirely
4. Add `argument-hint` to workon, roadmap, and backfill-spec

### Do soon (medium-value, medium-effort)

5. Add empty-diff and dirty-tree guards to commit skill
6. Add dependency reference validation to roadmap skill
7. Add TypeScript verification step to workon (for web tickets)
8. Add conflict resolution guidance to backfill-spec step 1
9. Standardize "offer to commit" phrasing across all skills

### Consider (lower priority, worth discussing)

10. Explore `context: fork` for read-heavy skill phases
11. Create a shared git-preflight reference
12. Add a README index to `.claude/skills/shared/`
13. Extend `tickets.py` to cover validation logic currently in skill prose
14. Add a TypeScript section to testing.md (or a separate testing-web.md)
15. Consider whether `Bash(source *)` permission is intentionally broad
