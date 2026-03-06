# Referential Integrity in Instruction Markdown

Research conducted 2026-03-02. Context: During a directory rename (`agent/plans/` to `agent/tickets/`), we discovered that cross-file path references in instruction markdown (skills, tickets, SPEC.md, CLAUDE.md) are a silent failure mode. Unlike code — where compilers, type checkers, and tests catch broken references — instruction markdown fails silently: the LLM reads stale paths, goes to the wrong place, or makes confident decisions based on outdated instructions. The failure is invisible until someone notices degraded behavior they can't attribute to a cause.

## The problem

Placeframe uses plain markdown files as executable instructions for an AI agent (Claude Code). These files contain literal file paths embedded in prose:

```markdown
Read frontmatter from all `agent/tickets/t*.md` files using the
`parse_frontmatter()` pattern from `scripts/src/scripts/tickets.py`.
```

When a directory is renamed, every file that references the old path must be updated. In code, this is mechanical — rename a module, update imports, the compiler tells you what you missed. In instruction markdown, there is no compiler. A stale path doesn't produce an error; it produces subtly wrong LLM behavior.

During the `agent/plans/` → `agent/tickets/` rename, we updated references across ~15 files (skills, tickets, SPEC.md, CLAUDE.md, Python and TypeScript source). The code changes were safe — type checkers and imports enforce correctness. The prose changes were not — we used find-and-replace across instruction files with no way to verify we didn't break the meaning.

## Why this is different from documentation rot

Traditional documentation rot (docs falling out of sync with code) is a well-known problem. But instruction markdown has a worse failure mode:

- **Stale documentation**: a human reads it, notices something looks off, checks the code, moves on.
- **Stale instruction markdown**: an LLM reads it, follows it confidently, produces wrong output. The LLM won't necessarily flag the inconsistency — it adapts and works with whatever it reads.

The consumer of these files is not a human who can exercise judgment. It's an LLM that treats every instruction as equally authoritative.

## The solution shape

This is a solved problem in documentation-as-code systems. The solution is always the same shape: prose contains symbolic references, a build step resolves them, and validation happens at build time.

### Prior art

| System | Mechanism | Validation |
|---|---|---|
| Sphinx (Python docs) | `:ref:` cross-references, `.. include::` directives | Build-time link validation, warnings for broken refs |
| Hugo / Jekyll | Template variables (`{{ .Site.BaseURL }}`) | Build fails on undefined variables |
| Docusaurus | File-path-based links, `@site/` prefix | Build-time broken link detection |
| MDX | JavaScript imports and interpolation in markdown | Standard JS module resolution |
| AsciiDoc | Attributes (`:project-name: Placeframe`) substituted in prose | Preprocessor validates before rendering |

All of these separate the *definition* of a reference (one place) from its *usage* (many places). A rename changes the definition; usages are resolved automatically.

### What it would look like for instruction markdown

```yaml
---
name: workon
vars:
  tickets_dir: agent/tickets
  tickets_glob: agent/tickets/t*.md
  plans_dir: agent/plans
---

Read frontmatter from all `{tickets_glob}` files...
Write the plan to `{plans_dir}/t{N}-plan.md`...
```

A rename changes one YAML value. A preprocessor interpolates before the LLM sees the content. A linter validates that all referenced paths exist.

## Why we can't do this today

Claude Code's skill loader passes raw markdown to the LLM. There is no preprocessing step between "read SKILL.md from disk" and "include in prompt." The frontmatter is parsed for `name` and `description` but arbitrary fields are not interpolated into the body.

Claude Code is source-available (GitHub: anthropics/claude-code) but not open source (all rights reserved under Anthropic's Commercial Terms). Forking is legally murky.

### Available extension points (as of March 2026)

- **Hooks**: Shell commands triggered by events (tool calls, notifications). No `skill-load` hook exists that could preprocess markdown before it reaches the LLM.
- **MCP servers**: Could theoretically serve interpolated skill files, but skills are loaded from disk by the skill system, not via MCP.
- **Upstream contribution**: An issue or PR for frontmatter variable interpolation in the skill loader would be a small, well-scoped feature.

## Partial mitigations without source changes

### 1. Convention + linting (weak guarantee)

A script that scans instruction markdown for backtick-wrapped strings that look like paths and checks whether they exist on the filesystem. Would catch `agent/plans/` references after a rename. Would not catch semantic errors (path exists but is wrong in context).

Challenges: distinguishing paths from code snippets, commands, and symbolic references (`$lib/`, `process.cwd()`). High false-positive rate without significant heuristics.

### 2. Single source of truth for paths (convention-based)

A shared file (e.g., `.claude/skills/shared/paths.md`) defines all canonical paths. Skills and tickets reference it. The LLM reads it alongside every skill. A rename updates one file.

Problem: prose still contains literal paths for readability. The shared file reduces the blast radius but doesn't eliminate it. Drift between the canonical file and prose references is still possible.

### 3. Minimize cross-file path references (discipline-based)

Accept that instruction markdown has this limitation and adopt a principle: avoid embedding literal paths in prose where possible. Use descriptions ("the tickets directory") rather than paths (`agent/tickets/`). When paths are necessary, concentrate them in structured sections (frontmatter, bulleted lists) rather than scattering through narrative prose.

This reduces the surface area for renames but doesn't eliminate the problem.

## Current decision

No tooling built. The rename that surfaced this problem is a rare, high-impact event — structural renames of top-level directories happen infrequently. The correct near-term mitigation is awareness and care during renames, not infrastructure.

The insight is captured here for when Claude Code's extension points mature (hooks, skill preprocessing) or if we decide the problem is frequent enough to warrant a preprocessing build step.

## Open questions

- Would Anthropic accept a PR for frontmatter variable interpolation in the skill loader? The feature is small and general-purpose.
- Is there a hooks-based workaround we haven't considered? The hooks system is relatively new and may gain new event types.
- If we build a preprocessing step, does that violate the "no ephemeral code artifacts" principle? The rendered markdown would be a generated file. Could be acceptable if the template is the source of truth and rendering is idempotent.
- Is this problem unique to Claude Code, or does every AI agent framework with file-based instructions face it? If universal, there may be emerging solutions in the broader ecosystem.
