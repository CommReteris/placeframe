---
id: T58
title: Create /audit skill for evaluating codebase artifacts against guidelines
status: design-needed
depends_on: []
---

# T58: Create /audit skill for evaluating codebase artifacts against guidelines

## Goal

Create a skill that systematically evaluates a set of codebase artifacts (skills, tickets, code files, configs) against stated criteria, presents prioritized findings, and optionally fixes them with user approval.

## Context

Two audits were conducted in the session that produced this ticket — a skill audit (all SKILL.md files against skill-authoring.md) and a ticket audit (all open tickets against ticket-format.md sizing rules). Both followed the same pattern:

1. Identify criteria (a reference doc to evaluate against)
2. Read every instance of the thing being audited
3. Evaluate each against the criteria, classify by priority (HIGH/MEDIUM/LOW)
4. Write findings to disk for user review
5. User approves which findings to act on
6. Fix the approved items
7. Delete the audit file after findings are acted on

This pattern will recur — the user wants to audit code against conventions, configs against standards, etc. A skill would formalize the process and prevent mistakes like the T27 incident (see below).

**Counter-training convention audits.** A specific high-value use case: auditing generated code against CLAUDE.md conventions that conflict with LLM training priors (inline aggressively, no decorative comments, no unnecessary abstractions, etc.). These conventions are reliably violated because generation-time priors override instructions. A shared criteria doc at `.claude/skills/shared/audit-conventions.md` (created by T59) will codify these conventions with detection guidance and before/after examples. The `/audit` skill should be able to use it as a criteria doc like any other.

### Key design inputs from the session

**Cross-reference existing tickets before fixing.** During the skill audit, `disable-model-invocation: true` was added to four skills without checking that T27 (a blocked ticket) already tracked that exact work and was blocked on an upstream bug. The audit skill must search existing tickets for overlap before implementing any fix. If a blocked ticket already tracks the same change, surface it as a finding rather than implementing.

**Two-phase structure with a user gate.** Findings and fixes are distinct phases. The user reviews all findings before any changes are made. Writing findings to a temporary file at workspace root worked well — the user could see the full picture before approving. This is a legitimate exception to the "no ephemeral artifacts" principle: the audit file exists for human review, not machine consumption, and is deleted after acting on findings.

**Audits need explicit criteria.** Both audits had a reference doc to evaluate against (skill-authoring.md, ticket-format.md). An audit without stated criteria is just "look at things." The skill should require specifying what you're auditing against — either a reference doc path or user-provided criteria.

**Prose and code audits differ in the fix phase.** Prose fixes are direct edits. Code fixes may need tests, linting, type checking. The findings phase is structurally identical for both. The fix phase needs to branch based on artifact type.

**The fix phase may or may not belong in this skill.** The session's fix phase was ad-hoc — direct edits after reviewing findings. A more structured approach: audit produces findings, each finding becomes a task, tasks get worked. But this may be over-engineering for common cases like "change 6 description fields." Open question for design discussion.

## Key files

- `.claude/skills/audit/SKILL.md` — new skill
- `.claude/skills/shared/skill-authoring.md` — reference for invocation model, description conventions
- `.claude/skills/shared/audit-conventions.md` — counter-training convention criteria doc (created by T59)

## Done when

- `/audit` skill exists with explicit criteria requirement, two-phase structure, and existing-ticket cross-referencing
- Skill handles both prose and code artifacts
- Findings are written to a temporary file with priority classification
- User gate between findings and fixes
- Temporary audit file is deleted after findings are acted on
