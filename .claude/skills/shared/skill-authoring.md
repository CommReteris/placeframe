# Skill Authoring Principles

## Cost model

Skill descriptions (~50-100 tokens each) are loaded into context on every message — they're how Claude decides which skill to invoke. Skill bodies (the full SKILL.md) load only when invoked. Shared reference files load only when the skill reads them. CLAUDE.md loads on every message in its entirety.

Budget: Claude Code allocates 2% of the context window for skill descriptions. If total descriptions exceed this, some skills get silently excluded. Check with `/context`.

## When to use CLAUDE.md vs a skill

- **CLAUDE.md**: Universal conventions that apply to every interaction regardless of task. Code style, project principles, naming rules. Keep it minimal — every token costs context on every turn, and instruction compliance degrades as it grows.
- **Skill**: A procedure triggered by a specific intent. Workflows, multi-step processes, domain-specific operations. Only loaded when needed.
- **Neither**: If a linter or formatter can enforce it deterministically (Ruff, ESLint, CSharpier), don't spend context budget on instructions. Tools are more reliable than instructions.

## Description

The `description` frontmatter field is the single most important factor for reliable activation. Claude matches user intent against description text — no embeddings, no classifiers, just the transformer reading the string.

- Write in third person: "Stage and commit current changes" not "I can help you commit."
- Include "Use when..." trigger phrases with concrete examples of user intents that should activate the skill.
- Be specific: "Stage and commit current changes with a well-crafted message" not "Helps with git."
- Set `disable-model-invocation: true` for side-effect workflows where timing matters (deploys, destructive operations) — this removes the skill from context entirely until the user explicitly invokes it.

## Instruction style

**Match specificity to task fragility.** Three levels:

- **Low freedom** (rigid steps): When operations are fragile, consistency is critical, or a specific sequence must be followed. Example: `/commit` — step-by-step with explicit commands.
- **Medium freedom** (templates with parameters): When a preferred pattern exists but some variation is acceptable. Example: `/roadmap create` — structured workflow with judgment calls.
- **High freedom** (end-state descriptions): When multiple approaches are valid and context determines the best one. Example: `/research` — describe what to produce, let Claude figure out how.

**Other rules:**

- Imperative voice: "Read the file" not "You should read the file."
- Don't explain what Claude already knows. Challenge each paragraph: "Does Claude need this explained?" Don't describe what git staging is. Don't explain what markdown is. Only add context Claude doesn't already have — project-specific conventions, non-obvious constraints, domain knowledge unique to this codebase.
- State preconditions explicitly. Agents eagerly execute. Clarify when NOT to act.
- Pick one term and use it consistently. Don't alternate between "API endpoint" / "route" / "URL" / "path" within the same skill.

## Progressive disclosure

Three layers, matching Claude Code's loading architecture:

1. **Description** (always loaded): ~50-100 tokens. Name + what it does + when to use it.
2. **SKILL.md body** (loaded on invocation): Under 500 lines. The full procedure.
3. **Shared reference files** (loaded when read): Supporting conventions, style guides, format specs. Referenced from SKILL.md via markdown links.

Keep references **one level deep** from SKILL.md. Deeply nested references (shared file → another shared file → another) cause partial reads. If a reference file exceeds 100 lines, add a table of contents at the top.

Use `.claude/skills/shared/` for references used by multiple skills (commit-style.md, ticket-format.md). Keep skill-specific references in the skill's own directory.

## Examples in skill prose

Examples are powerful for formulaic outputs — commit messages, file naming, frontmatter structure. They anchor Claude to a concrete pattern.

Examples are risky for high-variance outputs — plans, research reports, design discussions. Claude overfits to the example's structure, producing output that mimics the form even when the content demands a different shape.

Rule of thumb: if the output has a fixed format, show an example. If the output varies by context, describe the qualities you want instead.

## Anti-patterns

1. **Context bloat.** Treating CLAUDE.md or skills as a hotfix repository where every behavior correction gets appended. Instructions accumulate, contradict, and degrade compliance uniformly. Audit periodically.
2. **Semantic duplication.** Restating the same rule in different words across CLAUDE.md, skills, and shared refs. When phrasings differ slightly, Claude silently picks one interpretation. Single source of truth, reference don't repeat.
3. **Over-specification.** So much detail the agent has no room for judgment. If unexpected scenarios arise, rigid instructions collapse. Constrain only what's genuinely fragile.
4. **Under-specification.** Vague instructions expecting Claude to divine intent. "Handle the data appropriately" is not a useful instruction.
5. **Offering multiple approaches.** "You can use X, Y, or Z" forces a choice the agent shouldn't have to make. Provide a default with an escape hatch for specific cases.
