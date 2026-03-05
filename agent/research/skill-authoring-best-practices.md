# Skill Authoring Best Practices for Claude Code

Research conducted 2026-03-02. Context: creating a skill-authoring principles reference for the Placeframe project.

## The question

How should custom skills be written for Claude Code? What are the best practices for descriptions, instruction style, context budget, and progressive disclosure?

## Findings

### Invocation mechanics

Skills operate through a meta-tool system. At startup, only name + description (~50-100 tokens per skill) appear in context. When Claude decides to invoke a skill, the full SKILL.md loads (500-5000 tokens). Referenced files load on-demand after that. No embeddings or classifiers — Claude's transformer forward pass matches user intent against description text.

Budget: 2% of context window for skill descriptions. If exceeded, skills get silently excluded. Check with `/context`.

### Description quality

The single most important factor for reliable activation. Scott Spence's testing: properly optimized descriptions improved activation from 20% to 90%. Key rules from Anthropic:
- Write in third person
- Include "Use when..." trigger phrases with concrete examples
- Be specific about what the skill does

`disable-model-invocation: true` removes a skill from context entirely (zero cost until user explicitly invokes). Use for side-effect workflows where timing matters.

### Context budget: CLAUDE.md vs skills

- **CLAUDE.md**: Loaded on every message. Keep under 300 lines (HumanLayer recommendation). Instruction compliance degrades as it grows — models "begin to ignore all of them uniformly" rather than selectively.
- **Skills**: Two-tier cost. Description always in context (~50-100 tokens). Body loads only on invocation.
- **Neither**: If a linter can enforce it, don't spend context budget on instructions.

### Degrees of freedom framework (Anthropic)

Match instruction specificity to task fragility:
- **Low freedom** (rigid steps): Fragile operations, consistency critical. Example: commit workflows.
- **Medium freedom** (parameterized templates): Preferred pattern exists but variation acceptable. Example: ticket creation.
- **High freedom** (end-state descriptions): Multiple valid approaches. Example: research, planning.

Analogy: narrow bridge with cliffs = low freedom, open field = high freedom.

### Progressive disclosure

Three layers matching Claude Code's architecture:
1. **Index** (always loaded): Descriptions. ~50-100 tokens.
2. **Details** (on invocation): SKILL.md body. Under 500 lines.
3. **Deep dive** (on demand): Referenced files. One level deep from SKILL.md — deeply nested references cause partial reads.

### Anti-patterns (from multiple sources)

1. **Context bloat**: Accumulating instructions without auditing.
2. **Semantic duplication**: Same rule in different words across files.
3. **Over-specification**: No room for agent judgment.
4. **Under-specification**: Vague instructions expecting intent divination.
5. **Explaining what Claude already knows**: Challenge each paragraph.
6. **Deeply nested references**: Keep one level deep.
7. **Time-sensitive information**: "Before August 2025, use X" goes stale.
8. **Inconsistent terminology**: Pick one term, use it everywhere.
9. **Offering multiple approaches**: Provide a default, not a menu.
10. **Punting errors**: Verbose validation messages improve self-correction.

### Comparable systems

- **Cursor**: Four rule modes (Always Apply, Apply Intelligently, Apply to Specific Files, Apply Manually) map to CLAUDE.md, auto-invoke skills, glob-scoped rules, manual-only skills.
- **Aider**: Simple CONVENTIONS.md loaded via `--read`. Community-maintained convention files.
- **Cline Memory Bank**: File-based context persistence across sessions. Different paradigm — agent maintains its own state files.

## Sources

- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills)
- [Skill Authoring Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Claude Agent Skills: A First Principles Deep Dive (Lee Han Chung)](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
- [How to Make Claude Code Skills Activate Reliably (Scott Spence)](https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably)
- [Effective Context Engineering for AI Agents (Anthropic)](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Context Engineering for Coding Agents (Martin Fowler)](https://martinfowler.com/articles/exploring-gen-ai/context-engineering-coding-agents.html)
- [Spotify: Context Engineering for Background Coding Agents](https://engineering.atspotify.com/2025/11/context-engineering-background-coding-agents-part-2)
- [Writing a Good CLAUDE.md (HumanLayer)](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
- [Your Agent's Context Is a Junk Drawer (Augment Code)](https://www.augmentcode.com/blog/your-agents-context-is-a-junk-drawer)
- [Claude Code Customization Guide (Alex Op)](https://alexop.dev/posts/claude-code-customization-guide-claudemd-skills-subagents/)
