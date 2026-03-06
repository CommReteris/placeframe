# Structured Markdown Tickets: Research Survey

Research conducted 2026-02-28. Context: Placeframe's roadmap tickets are plain markdown files in `agent/plans/`. They work well for prose (context, implementation plans, acceptance criteria) but lack schematic structure for programmatic interaction — filtering by status, resolving dependency graphs, listing blocked tickets. We researched how others add structure to markdown-based ticketing without abandoning the prose-friendly format.

## The question

How do you make a folder of markdown ticket files queryable like a database while keeping them human-editable and LLM-readable?

## The consensus answer: YAML frontmatter

Every tool and pattern surveyed converges on the same approach: YAML frontmatter for machine-readable fields, markdown body for prose. The frontmatter block (`---`-delimited) is universally understood by parsers, renderers (GitHub, VS Code, Jekyll, Hugo), and AI agents.

Representative schema (from taskmd, Feb 2026):

```yaml
---
id: task-001
title: "Add linting to CI"
status: todo          # todo | in_progress | done | blocked | cancelled
priority: high        # high | medium | low
effort: small         # small | medium | large
tags: [ci, devops]
dependencies: [task-002, task-003]
---
```

The body below holds objectives, acceptance criteria, notes, references. Tools operate on the frontmatter; humans and LLMs operate on the body.

---

## A. Markdown-based project management tools

### Markdown Projects (mdp)

Website: markdownprojects.com. Stores everything in `.mdp/` as plain markdown with YAML frontmatter. Fields: `id`, `title`, `type`, `status`, `priority`, `labels`, `assignee`, `milestone`, `checklist`. CLI: `mdp issue list`, `mdp issue update`, `mdp issue get`. Returns structured JSON. No native dependency graph. Imposes its own directory structure.

### taskmd

DEV Community / Medium articles (Feb 2026). Designed explicitly for AI coding agents. YAML frontmatter with `id`, `status`, `priority`, `effort`, `tags`, `dependencies`. The pitch: agents can read frontmatter to understand task state without ingesting the full prose body.

### wedow/ticket

GitHub: wedow/ticket. Single bash script. Tickets are markdown files with YAML frontmatter in `.tickets/`. Explicitly designed so "AI agents can easily search them for relevant content without dumping large context into their context window." Has dependency graph support, priority levels, zero setup.

### Tasks.md

GitHub: BaldissaraMatheus/Tasks.md. Self-hosted Kanban board backed by plain markdown files. More UI-focused, less CLI/query-focused.

### TrackDown

GitHub: mgoellnitz/trackdown. Uses a single `issues.md` file with heading-based structure instead of frontmatter. Git hooks auto-update status from commit messages (`fixes #ID`). No dependency tracking.

---

## B. Git-native issue trackers

### git-bug

GitHub: git-bug/git-bug. Stores bugs in git objects (refs/bugs/), not working-tree files. Distributed and offline-first. Terminal UI, web UI, CLI. Bugs travel with the repo on clone. Tradeoff: you can't open a ticket in a text editor directly.

### git-issue

GitHub: dspinellis/git-issue. Issues stored as directories with multiple files inside git. More transparent than git-bug (actual files), but structured as a directory per issue. More complex than single-file-per-ticket.

### Sciit

Issues live as block comments inside source code itself. Interesting but impractical for prose-heavy planning tickets.

**Verdict on git-native tools**: They solve merge/branch correctness but sacrifice direct-editability and LLM-readability. Not the right fit for prose-heavy planning tickets.

---

## C. The Obsidian Dataview pattern

Obsidian Dataview is the reference implementation for treating a folder of markdown files as a queryable database. It indexes YAML frontmatter fields (automatically), inline fields with `[key:: value]` syntax, and implicit file metadata (tags, creation date, links).

Query syntax (DQL):

```
TABLE status, priority, depends_on
FROM "agent/plans"
WHERE status != "Done"
SORT priority ASC
```

Also supports full JavaScript (DataviewJS) for arbitrary computation.

**Critical limitation**: Only runs inside Obsidian. No standalone CLI.

### Standalone equivalents

**MarkdownDB** (GitHub: flowershow/markdowndb) — Node.js library that scans a directory of markdown files, extracts frontmatter and links, builds a local SQLite database. CLI: `npx mddb agent/plans/` produces `markdown.db`. Query with SQL:

```sql
SELECT file_path, json_extract(metadata, '$.status') as status
FROM files
WHERE json_extract(metadata, '$.status') != 'Done'
ORDER BY json_extract(metadata, '$.priority');
```

**python-frontmatter** (GitHub: eyeseast/python-frontmatter) — Python library that parses YAML frontmatter into dicts. A small script can load all files from a directory, filter by any field, sort, build dependency graphs. No database needed. Fits naturally into a `uv run` script.

**frontmatter CLI** (GitHub: rythoris/frontmatter) — Go CLI for reading/writing individual frontmatter fields. Useful for scripted updates: `frontmatter set status Done agent/plans/t1-linting-ci.md`.

**markdown-frontmatter MCP server** (GitHub: caffeinatedwes/markdown-frontmatter-mcp) — Wraps the frontmatter-query pattern for Claude Desktop and MCP clients. Exposes `query_recent_notes` with tag/date filtering over any markdown folder.

---

## D. AI/LLM-native approaches

### Pattern A: Markdown files as agent context

Example: snarktank/ai-dev-tasks. Pure markdown prompt files. No structured data; the agent reads prose instructions. No programmatic querying.

### Pattern B: YAML frontmatter for agent-readable structure

Examples: taskmd, wedow/ticket. The agent reads frontmatter to understand task state and dependencies without ingesting the full prose body. Designed so agents can enumerate tickets, check status, resolve dependencies, and update fields atomically.

### Pattern C: First-class typed task objects

Example: Augment Code Tasklist. Tasks are JSON objects with UUIDs, not markdown files. State machine: `todo → in_progress → finished/cancelled`. Enables real-time streaming updates, cross-session persistence, and deterministic metrics. Quote: "Moving from markdown to structured schema unlocks deterministic metrics and analytics." Cost: loses prose-friendly nature.

### Pattern D: Spec-driven development

Example: Kiro. Three markdown files per feature: `requirements.md`, `design.md`, `tasks.md`. Tasks get IDE-level execution UI. No queryable frontmatter — structure conveyed via markdown conventions.

---

## E. Hybrid approaches (sidecar index)

The MarkdownDB pattern: markdown files are source of truth, a generated SQLite database serves as query index. Rebuild with `npx mddb agent/plans/`, query with SQL.

Python-native equivalent: a script using `python-frontmatter` that loads all `.md` files, builds in-memory list of dicts, supports `--status`, `--blocked`, `--depends-on` filter flags. No database needed for a small ticket count.

---

## F. Practical assessment for Placeframe

### What fits

**YAML frontmatter + python-frontmatter script** is the clear winner for this repo:
- Python monorepo, already uses `uv run` scripts for everything
- 15 tickets — no need for SQLite, MarkdownDB, or any external tool
- `python-frontmatter` is a single pip dependency
- Frontmatter formalizes what's already in the prose (status, dependencies, goal)
- `roadmap.md` becomes derivable from frontmatter rather than manually maintained
- Skills (`/ticket`, `/intake`) can read and update frontmatter atomically

### What doesn't fit

- **git-bug / git-issue**: Sacrifice direct editability. Not worth it for prose-heavy tickets.
- **mdp / wedow/ticket**: Impose their own directory structures. Migration cost for no real gain over a custom script.
- **MarkdownDB / SQLite sidecar**: Overkill at this scale. Adds Node.js dependency.
- **Full JSON objects (Augment pattern)**: Loses prose-friendliness, which is the whole point.

### Suggested fields for frontmatter

```yaml
---
id: T14
title: Codebase sweep — harvest TODOs into tickets
status: plan-needed    # design-needed | plan-needed | ready | blocked | done
depends_on: []         # list of ticket IDs, e.g. [T10, T12]
---
```

Keep it minimal. `priority` and `effort` can be added later if needed. Don't frontload fields you won't query.

### Implementation path (in order of ambition)

1. **Add frontmatter to ticket files**, keep `roadmap.md` manual, query when needed
2. **Add frontmatter + `uv run roadmap` query script** — filter/sort/list tickets programmatically
3. **Generate `roadmap.md` from frontmatter** — single source of truth in ticket files

Option 2 is the right next step. Option 3 is the natural endpoint once the script proves useful.

---

## Sources

- taskmd — Task management for the AI era (Medium, Feb 2026)
- DEV Community: "I Built a Task Manager for the AI Coding Era" (Feb 2026)
- Markdown Projects: markdownprojects.com
- wedow/ticket: github.com/wedow/ticket
- git-bug: github.com/git-bug/git-bug
- TrackDown: github.com/mgoellnitz/trackdown
- Obsidian Dataview documentation: blacksmithgu.github.io/obsidian-dataview
- MarkdownDB: github.com/flowershow/markdowndb
- markdown-frontmatter MCP server: github.com/caffeinatedwes/markdown-frontmatter-mcp
- python-frontmatter: github.com/eyeseast/python-frontmatter
- snarktank/ai-dev-tasks: github.com/snarktank/ai-dev-tasks
- Augment Code: "How we built Tasklist" (augmentcode.com)
- Kiro Specs documentation: kiro.dev/docs/specs
- AGENTS.md open format: agents.md
- Martin Fowler: "Exploring Gen AI — SDD Tools" (martinfowler.com)
