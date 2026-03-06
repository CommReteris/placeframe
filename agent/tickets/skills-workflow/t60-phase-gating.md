---
id: T60
title: Deterministic phase gating for long sequential skills
status: design-needed
depends_on: []
---

# T60: Deterministic phase gating for long sequential skills

## Goal

Solve instruction-following degradation in long sequential skills by introducing deterministic phase transitions, without assuming the solution must live within Claude Code's current capabilities.

## Context

The `/workon` skill is now 10 steps / 180 lines, with sub-steps and branching. It works today, but the architecture has a structural fragility: by the time the agent reaches late steps (7–10: capture learnings, spec maintenance, submit, commit), the skill instructions are far back in context and competing with a large volume of implementation content. Late steps are the most likely to be skipped or half-executed.

**The problem is not "workon is too long."** It's that sequential instruction following degrades over context distance, and Claude Code has no mechanism for deterministic phase transitions. This is a tool-level constraint, not a skill-authoring problem. Attempting to fix it purely through better skill prose (shorter steps, checklists, restructuring) addresses symptoms, not the cause.

### Solution patterns evaluated

Four approaches were considered. Each has a fundamental limitation:

1. **Compact checklists at the end.** Replace late-step prose with a terse checklist the agent runs through mechanically. *Problem:* Still suffers from context distance. A checklist 50k tokens back is no more likely to be followed than prose 50k tokens back. Cosmetic fix.

2. **Phase gates with re-injection.** Split the workflow into phases. At the transition point, explicitly re-read the skill file so instructions are fresh in context. *Problem:* "Re-read this file now" is a soft instruction. The model might comply, might not. Even when it does, the earlier context still competes for attention. This is the correct architecture but cannot be implemented deterministically within Claude Code today.

3. **Separate skills chained by the user.** Split `/workon` into `/workon` (build + verify + audit) and `/ship` (learnings + spec + submit + commit). Each skill loads fresh instructions. *Problem:* Shifts the burden to the user to remember and invoke the second skill. Effectively option 2 but the user is the phase gate.

4. **Exit checklist pattern.** The skill focuses on core work and ends with a compact block: "Before offering to commit, verify: [ ] Log written, [ ] Observations written, [ ] Spec checked, [ ] Learnings reviewed." *Problem:* Less thorough than dedicated steps. Same context distance issue in a slightly smaller package.

**Assessment:** Options 1 and 4 are cosmetic — they reformat the instructions but don't solve the structural problem. Option 3 works but imposes user burden. Option 2 is architecturally correct but not robustly implementable today. All options within Claude Code's current constraints are nondeterministic.

### The design axis

The real split is between steps that **require judgment** and steps that **could be deterministic**:

| Step | Type | Could be deterministic? |
|------|------|------------------------|
| Capture learnings | Judgment | No — requires evaluating whether failures are generalizable |
| Spec drift detection | Judgment | No — requires comparing prose to code semantics |
| Write Log section | Mechanical | Yes — structured output from known inputs |
| Write Observations section | Mechanical | Yes — structured output from audit step |
| Verify step numbering | Mechanical | Yes — pattern matching |
| Run linters/tests | Mechanical | Yes — shell commands with pass/fail |

A future solution should make the deterministic parts truly mechanical (guaranteed execution, not instruction-following) while still using the LLM for the judgment parts. The judgment steps might still degrade, but the mechanical steps — which are the ones most commonly skipped today — would be reliable.

### Tools that could change the equation

This ticket should not be tackled until the available tooling is known. Possibilities:

- **Claude Code native phase gates or context:fork** (T33) — upstream feature that would allow spawning a sub-invocation with scoped context
- **External workflow orchestrator** — a deterministic shell script or tool that invokes Claude Code N times with scoped prompts, handling phase transitions outside the model
- **Enhanced MCP servers or hooks** — if hooks gain enough capability to enforce checkpoints or inject instructions at specific points
- **Something that doesn't exist yet** — the tool landscape is moving fast

## Key files

- `.claude/skills/workon/SKILL.md` — the skill that needs phase gating
- `.claude/skills/shared/skill-authoring.md` — will need updating if the solution introduces new skill patterns

## Done when

- A design is chosen that makes mechanical steps deterministic (not instruction-dependent)
- The design accounts for judgment steps that must remain LLM-driven
- `/workon` late steps (7–10) execute reliably without user nudging
