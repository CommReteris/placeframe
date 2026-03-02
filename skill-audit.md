# Skill Audit

Audit of all existing skills against `.claude/skills/shared/skill-authoring.md` principles.

Prioritized: HIGH items should be fixed. MEDIUM items are worth fixing if we're already editing the file. LOW items are noted but not actionable now.

---

## /commit (31 lines)

**Description**: "Stage and commit current changes with a well-crafted message. Smarter replacement for quick WIP commits — actually reads diffs to write accurate messages."
- MEDIUM: Missing "Use when..." trigger phrase. Could add: "Use when the user says 'commit this', asks to save changes, or after completing a task."
- LOW: "Smarter replacement for quick WIP commits" is marketing copy, not a trigger phrase. Doesn't hurt but wastes description budget.

**Body**: Clean. Good progressive disclosure (refs commit-style.md, git-preflight.md). Low freedom (rigid steps) — appropriate for a fragile, side-effect operation. 31 lines is tight.

**No issues found.**

---

## /tidy-commits (79 lines)

**Description**: "Reorganize commits on the current branch into clean, logical commits for PR review. Use when the user wants to clean up history before merging."
- Good: Has "Use when..." trigger phrase.

**Body**:
- MEDIUM: Semantic duplication — "Preserve original commit authors" appears twice: once in the field reference for `author` (line 54) and again as a standalone bullet (line 60). The standalone bullet is redundant.
- MEDIUM: The "Important rules" section at the bottom (lines 74-79) mixes preconditions ("NEVER use git rebase -i") with edge case handling ("If the branch has only 1 commit"). These are different concerns — the preconditions could be in a pre-flight step, and the edge case is a decision point in step 2.
- LOW: Line 27 says "Do NOT present the plan for conversational approval" and line 62 repeats the same instruction. Semantic duplication.

---

## /allow-tool (53 lines)

**Description**: "Add a permission rule to .claude/settings.json so a previously-prompted tool is auto-allowed in future sessions."
- MEDIUM: No "Use when..." trigger. Should add: "Use when the user encounters a tool permission prompt they want to auto-allow."

**Body**:
- HIGH: The "Permission strategy" section (lines 8-18) explains the project's security model. This is valuable context but it's **project-level design rationale, not skill instructions**. It would be better in a shared reference or CLAUDE.md. Every time /allow-tool is invoked, these 10 lines of philosophy load into context — but they're also relevant to understanding /commit and /tidy-commits gate design. Moving to a shared ref would let multiple skills reference it without duplication.
- LOW: The command classification lists (lines 26-44) are thorough but long. Claude likely knows most of these categories already — this approaches "explaining what Claude already knows" territory. However, the project-specific decisions (what's pre-approved vs not) are genuinely non-obvious, so this is borderline justified.

---

## /roadmap (62 lines)

**Description**: "Create, import, query, and reorganize tickets on the Placeframe roadmap."
- HIGH: Description is too vague for reliable activation. "Create, import, query, and reorganize tickets" doesn't include trigger phrases. Should include: "Use when the user wants to create a ticket, import tickets from a list, query ticket status, or reorganize the roadmap."
- MEDIUM: Missing `argument-hint`. The skill takes arguments like "create", "import", "query", "reorganize" — the hint should show these.

**Body**: Clean structure, medium freedom (appropriate — structured workflow with judgment). Good sizing check additions from T46.

---

## /workon (161 lines)

**Description**: "Pick up and work on a roadmap ticket."
- HIGH: Description is too terse. "Pick up and work on a roadmap ticket" doesn't convey the full scope (TDD, planning, spec maintenance, learning capture). More importantly, it lacks trigger phrases. Should add: "Use when the user says 'work on T4', 'pick up a ticket', or wants to implement a roadmap item through the full lifecycle."

**Body**:
- HIGH: At 161 lines, this is the largest skill. While under the 500-line limit, it's dense and covers 9 major steps. The concern isn't size per se — it's that context capacity is consumed every time the skill fires, including for simple ticket status checks. Consider whether the status-check logic (step 3's `blocked`/`in-review`/`done` branches) could be simpler, since those paths do almost nothing but the full 161-line body still loads.
- MEDIUM: Step 3 "Check status and act" has a `design-needed` branch that says "Proceed to step 4" — but step 4 is the TDD cycle. For `design-needed` tickets, the actual next step is discussing open questions and moving to `plan-needed`. The "Proceed to step 4" reference is wrong; it should say "Proceed to step 3a after status update." **This is a bug.**
- MEDIUM: The RED phase (step 4) is heavily specified — 6 detailed sub-steps. This is appropriate for TDD (fragile, consistency matters), but sub-step 3 ("Add additional tests for edge cases, error handling, and implementation details the criteria don't explicitly mention") contradicts the earlier instruction to "Focus exclusively on the 'Done when' criteria and spec behaviors." These are conflicting instructions — one says focus exclusively, the other says go beyond. Claude silently picks one.
- MEDIUM: Step 6 (Capture learnings) and Step 7 (Spec maintenance) are post-implementation housekeeping that loads into context during planning and implementation phases when it's irrelevant. Not actionable now, but if workon ever gets refactored, these could be separate skills invoked at the end.

---

## /research (80 lines)

**Description**: "Open-ended brainstorming interview followed by web/codebase research, producing a report in agent/research/."
- MEDIUM: No "Use when..." trigger. Could add: "Use when the user wants to investigate a topic, compare tools, or gather information before making a decision."

**Body**: Good structure, high freedom (appropriate — research is inherently open-ended). The report format section (lines 43-67) includes a template example, which is borderline per the examples guideline — research reports are high-variance outputs. However, the template is explicitly marked "adapt to fit the topic — these are common sections, not a rigid template," which mitigates the overfitting risk.

**No major issues.**

---

## /backfill-spec (79 lines)

**Description**: "Retroactively create a SPEC.md for a feature directory that predates the spec convention."
- MEDIUM: No "Use when..." trigger. Could add: "Use when a feature directory has code but no SPEC.md and needs one backfilled."

**Body**: Well-structured, medium freedom. Good progressive disclosure (refs spec-format.md). The ownership model note (lines 13-14) is important context that justifies its inclusion.

**No major issues.**

---

## /debrief (40 lines)

**Description**: "Scan the conversation for uncaptured context before clearing. Surface decisions, insights, and loose threads that didn't land in a repo artifact."
- MEDIUM: No "Use when..." trigger. Could add: "Use before /clear or ending a session to capture decisions and insights."

**Body**: Clean, appropriate freedom level (medium — structured steps with judgment on what to surface). 40 lines is efficient.

**No issues found.**

---

## Shared reference files

- **ticket-format.md** (114 lines): Exceeds 100-line threshold. Per skill-authoring.md, should have a table of contents at the top.
- **testing.md** (90 lines): Approaching threshold. Fine for now.
- **All others**: Under 100 lines, no issues.

---

## Invocation model

Each skill should either auto-invoke (Claude fires it when user intent matches the description) or be manual-only (`disable-model-invocation: true`, zero context cost, user must type the slash command).

**Auto-invoke** — frequently used, natural-language triggering is valuable:
- `/commit` — user says "commit that," Claude fires the skill. Git commit permission is still the gate.
- `/workon` — "work on T46" is the primary entry point.
- `/roadmap` — "create a ticket for X" or "show me open tickets."
- `/research` — "research spatial anchor formats."

**Manual-only** — rare, sensitive, or explicitly user-initiated:
- `/tidy-commits` — CLAUDE.md says "never offer /tidy-commits, always user-initiated." History rewriting should never be Claude's idea.
- `/allow-tool` — Claude should not auto-decide to relax its own permissions.
- `/debrief` — user decides when to debrief. Auto-firing mid-conversation would be unwelcome.
- `/backfill-spec` — rare, heavyweight, requires sustained user participation.

Budget impact: 4 skills in the always-loaded description budget (~200-400 tokens/message), 4 removed entirely (zero cost until explicitly invoked).

---

## Summary: HIGH priority

| Skill | Issue | Fix |
|---|---|---|
| /workon | Description too terse, no trigger phrases | Expand description |
| /workon | Step 3 `design-needed` says "Proceed to step 4" — should be step 3a | Fix reference |
| /roadmap | Description too vague, no trigger phrases, missing argument-hint | Expand description, add hint |
| /allow-tool | Permission strategy section is project-level design rationale, not skill instructions | Consider moving to shared ref |
| /tidy-commits | Should be manual-only but `disable-model-invocation` has upstream bugs (T27) | Deferred to T27 |
| /allow-tool | Should be manual-only but `disable-model-invocation` has upstream bugs (T27) | Deferred to T27 |
| /debrief | Should be manual-only but `disable-model-invocation` has upstream bugs (T27) | Deferred to T27 |
| /backfill-spec | Should be manual-only but `disable-model-invocation` has upstream bugs (T27) | Deferred to T27 |

## Summary: MEDIUM priority

| Skill | Issue |
|---|---|
| /workon | RED phase has conflicting instructions (focus exclusively vs go beyond) |
| /workon | 161 lines — post-implementation steps load during planning |
| /tidy-commits | "Preserve original commit authors" duplicated (lines 54 and 60) |
| /tidy-commits | "Do NOT present the plan" duplicated (lines 27 and 62) |
| /commit | Missing "Use when..." trigger |
| /allow-tool | Missing "Use when..." trigger |
| /allow-tool | Command classification lists may over-explain |
| /research | Missing "Use when..." trigger |
| /backfill-spec | Missing "Use when..." trigger |
| /debrief | Missing "Use when..." trigger |
| ticket-format.md | Exceeds 100 lines, needs TOC |
