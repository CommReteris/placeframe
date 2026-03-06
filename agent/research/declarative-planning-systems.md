# Declarative Planning Systems for AI Agents: Research Survey

Research conducted 2026-02-28. Context: Placeframe's roadmap and ticket system is currently expressed in English markdown. We want to understand what exists for expressing planning artifacts in declarative, validated, machine-readable formats that both humans and AI agents can work with efficiently.

## The question

Can we replace freeform markdown tickets with structured, lintable files where:
- Statuses must come from a defined enum
- Dependencies must reference existing targets
- Acceptance criteria are machine-verifiable
- Both humans and code can read/write the format efficiently

## The gap

As of early 2026, no tool combines all of:
1. Tasks as typed, structured files in a git repo
2. A formal schema with enums, constraints, and dependency graph validation
3. A linter that runs in CI
4. Designed for both human editing and AI agent consumption

The pieces exist. Nobody has assembled them for this use case.

---

## A. Issues and tickets as code

### git-bug

Distributed, offline-first bug tracker embedded in Git. Issues are stored as Git objects (not working-tree files), so they push/pull with code. Exposes a GraphQL API, terminal UI, web UI, and CLI. Bridges to GitHub, GitLab, Jira, Launchpad.

- **Maintainer**: git-bug org (originally Michael Mure). Go.
- **Status**: Active. Major 2024-2025 rework introduced immutable append-only DAG operations, reworked identity, generic entity package.
- **Schema/validation**: Typed operations (`SetTitle`, `AddComment`, `SetStatus`) enforced by Go types internally. No user-facing schema validator.
- **AI compatibility**: GraphQL API is agent-friendly. No built-in AI integration.
- **URL**: https://github.com/git-bug/git-bug

### git-issue

Shell-based decentralized issue management by Diomidis Spinellis. Issues stored as files in a hidden Git branch. Scriptable CLI, file-based storage. No schema validation.

- **Status**: Moderately maintained, infrequent updates.
- **URL**: https://github.com/dspinellis/git-issue

### Sciit (Source Control Integrated Issue Tracker)

Academic project embedding issues as structured block comments in source code. Metadata annotations (`@issue`, `@title`, `@priority`, `@due`, `@label`) inline with code. Git hooks track lifecycle.

- **Maintainer**: University of Glasgow researchers.
- **Status**: Not actively maintained (last ~2020-2021). Academic paper is the primary artifact.
- **URL**: https://sciit.gitlab.io/sciit/

### tickgit

Scans source code for `TODO`/`FIXME`/`HACK`/`XXX` comments and presents them as structured tickets with Git blame metadata. A scanner, not a task system.

- **URL**: https://www.tickgit.com/ and https://github.com/augmentable-dev/tickgit

### IssueOps (GitHub methodology)

Treats GitHub Issues as a command interface for automation. Issue forms use YAML schemas in `.github/ISSUE_TEMPLATE/`. GitHub Actions parse structured form data to trigger workflows. In January 2025, GitHub added sub-issues and structured issue types (bug, task, initiative) in public preview.

- **Validation**: GitHub validates issue form YAML against its form schema at PR time.
- **AI compatibility**: GitHub Copilot and agents already interact via `gh` CLI and API.

### Gitea / Forgejo

Self-hosted Git forges with built-in issue tracking, project boards, milestones, labels, time tracking, dependencies. Swagger/OpenAPI-documented REST APIs. Full-featured but conventional SaaS-style issue tracking.

- **URLs**: https://about.gitea.com/ | https://forgejo.org/

---

## B. AI agent task planning frameworks

### CrewAI

Python multi-agent orchestration with role-based agent definitions. Tasks and agents configured via YAML (`agents.yaml`, `tasks.yaml`). Task YAML includes `description`, `expected_output`, `agent`, `output_file`, `tools`, and `context` (task dependencies). Pydantic used internally for structured outputs.

- **Validation**: Runtime validation of YAML-to-object mapping (agent references, tool references, context task resolution). No standalone schema file published for external linting.
- **URL**: https://github.com/crewAIInc/crewAI

### LangGraph

Stateful graph-based agent workflows built on LangChain. Workflows modeled as state machines with nodes and edges (including cycles and conditionals). Code-first, not declarative-file-first. State is a typed dictionary or Pydantic model.

- **Validation**: State schema via Pydantic. Graph structure validated (nodes must exist, edges must reference valid nodes).
- **URL**: https://github.com/langchain-ai/langgraph

### Microsoft TaskWeaver

Code-first agent framework for data analytics. Two-layer planning: high-level planner + code generator/executor. Plugin definitions use YAML schemas. Rich data structures (DataFrames) are first-class.

- **URL**: https://github.com/microsoft/TaskWeaver

### Microsoft Semantic Kernel + Agent Framework

Production SDK for AI agents, merged with AutoGen. Supports declarative agent definitions in YAML/JSON with typed fields. Custom agents registered with `AgentRegistry`. Composable orchestration patterns (concurrent, sequential, handoff, group chat). Available in C#, Python, Java.

- **URL**: https://github.com/microsoft/semantic-kernel

### Shrimp Task Manager (MCP Server)

MCP server providing structured task management for AI coding agents. Converts natural language into structured dev tasks with dependency tracking, chain-of-thought planning, iterative refinement. MCP tools (`plan_task`, `analyze_task`, `split_tasks`, `execute_task`, `verify_task`, `reflect_task`) enforce a workflow. Tasks persist across sessions. Dependencies validated (targets must exist).

- **Status**: Active, community-forked for different languages and features.
- **AI compatibility**: Specifically designed for Claude Code, Cursor, and other MCP-compatible tools.
- **URL**: https://github.com/cjo4m06/mcp-shrimp-task-manager
- **Note**: This is the closest existing tool to "validated task planning for AI agents" but it's a runtime system, not a file-based declarative format.

### Claude Code Task System

Built-in `TaskCreate`/`TaskUpdate`/`TaskList`/`TaskGet` tools. Status enum (`pending` → `in_progress` → `completed`). Dependencies as task ID references. Tasks persist in `~/.claude/tasks/`. Same limitations as Shrimp: runtime system, not lintable files.

### CCPM (Claude Code Project Manager)

Uses GitHub Issues as source of truth and Git worktrees for parallel agent execution. Converts PRDs into epics → issues → code. Tasks can be marked `parallel: true` for concurrent development.

- **URL**: https://github.com/automazeio/ccpm

---

## C. Configuration languages (the validation layer)

These provide the type system and constraint validation infrastructure. None are currently used for project planning, but any could serve as a schema language for task definitions.

### CUE

Constraint-based data validation language rooted in logic programming. Superset of JSON. Types and values exist in a single lattice hierarchy. Validates against JSON, YAML, TOML, OpenAPI, Protobuf, JSON Schema.

- **Maintainer**: CUE project (originally Google, by Marcel van Lohuizen, co-creator of Go).
- **Status**: Active.
- **Cautionary tale**: Dagger (CI tool by Docker's creator) originally used CUE but dropped it, finding developers preferred general-purpose languages they already knew.
- **URL**: https://github.com/cue-lang/cue

### KCL (CNCF Sandbox)

Constraint-based record and functional language with static type system and compile-time validation. Similar goals to CUE but with OOP-inspired schema system and better performance at scale. `check` blocks embed validation rules directly in schemas.

- **Maintainer**: Ant Group (Alibaba), CNCF Sandbox project.
- **Status**: Very active.
- **URL**: https://github.com/kcl-lang/kcl

### Pkl (Apple)

Configuration-as-code with static typing, classes, functions, conditionals, constraints. Generates JSON, YAML, XML. Code generation for Java, Kotlin, Swift, Go.

- **Status**: Open-sourced February 2024, actively maintained.
- **URL**: https://github.com/apple/pkl

### Dhall

Programmable configuration language. Explicitly typed, guaranteed to terminate (not Turing-complete). Think "JSON + functions + types + imports." The termination guarantee is a safety property relevant to agent-consumed configs.

- **Status**: Maintenance mode. Core spec stable, reduced contribution pace.
- **URL**: https://github.com/dhall-lang/dhall-lang

### Jsonnet

Data templating language from Google extending JSON with variables, conditionals, functions, imports. Widely used (Databricks, Kubernetes/Tanka, Prometheus). No type system — errors caught at evaluation time only.

- **URL**: https://github.com/google/jsonnet

### JSON Schema (pragmatic baseline)

Not a language but a vocabulary for annotating and validating JSON. Widely supported, well-tooled, understood by everyone. Less expressive than CUE/KCL but vastly more accessible.

---

## D. Spec-driven development (the 2025 wave)

This area saw explosive growth in 2025 and is the most directly adjacent to our use case. These tools structure the *planning* phase of AI-assisted development but focus on natural-language specs rather than typed schemas.

### GitHub Spec Kit

Open-source (MIT) toolkit for spec-driven development. Templates, CLI, and prompts for GitHub Copilot, Claude Code, Gemini CLI. Four gated phases: Specify → Plan → Tasks → Implement. Tasks broken into "small, reviewable units that can be implemented and validated in isolation."

- **Status**: Released September 2025, active development.
- **Validation**: Phase gates enforced by CLI. Structure validated but content is natural language.
- **URL**: https://github.com/github/spec-kit

### Kiro (AWS)

AI coding IDE enforcing spec → design → tasks → implementation. `requirements.md`, `design.md`, `tasks.md` generated as structured artifacts. Given/When/Then acceptance criteria. Cloud-agnostic despite AWS origins.

- **Status**: Public preview mid-2025. Free tier (50 agent interactions/month), Pro ($19/month).
- **URL**: https://kiro.dev/

### Tessl

"Agent enablement platform" using specs as primary artifact. Aspires to "spec-as-source" where specs are maintained and code is marked `// GENERATED FROM SPEC - DO NOT EDIT`. Includes a Spec Registry for versioned, shared specifications. Martin Fowler's team analyzed it favorably.

- **Status**: Spec Registry in open beta, Framework in closed beta (late 2025).
- **URL**: https://tessl.io/ | https://docs.tessl.io/

### OpenSpec

Open-source SDD framework emphasizing "structure before code." Key innovation: **delta specs** for brownfield development — describe what is changing rather than restating the entire specification. Three-step: Proposal → Apply → Archive. Supports 20+ AI tools.

- **Maintainer**: Fission AI.
- **URL**: https://github.com/Fission-AI/OpenSpec

### BMAD Method

"Breakthrough Method for Agile AI-Driven Development." YAML-based multi-agent workflow with specialized roles (Analyst, PM, Architect, Scrum Master, Dev). Four-phase cycle: Analysis → Planning → Solutioning → Implementation. Scrum Master agent generates "hyper-detailed development stories."

- **Status**: Active (v5 current).
- **Closest to typed planning**: YAML workflow blueprints define task sequences, dependencies, and handoff points. But no formal schema validation.
- **URL**: https://github.com/bmad-code-org/BMAD-METHOD

---

## E. Hybrid human+machine planning formats

### Org-mode (Emacs)

The original "structured text that's both human-readable and machine-parseable." Headings, TODO states, tags, properties, scheduling, deadlines, priorities, inline code blocks. Custom TODO state sequences per file. Mature and stable.

- **AI integration**: The **org-mcp** project (2025) implements an MCP server exposing org files to AI assistants via JSON-structured URIs.
- **URL**: https://orgmode.org/ | https://github.com/laurynas-biveinis/org-mcp

### Taskwarrior

CLI task manager storing every task as a structured JSON object. Typed attributes: project hierarchy (dot notation), tags, due dates, urgency scores, dependencies, recurrence, custom UDAs. `task export` produces structured JSON.

- **Validation**: Field types enforced. UDAs have declared types. Dependencies reference existing UUIDs.
- **Most mature structured-data-first task manager**, but no AI features.
- **URL**: https://github.com/GothenburgBitFactory/taskwarrior

### Todo.txt

Minimal plain-text format. One task per line with optional structured metadata: `(A)` priority, `+Project` tags, `@Context` tags, `key:value` extensions. Trivially parseable. Too simple for complex planning (no dependencies, no hierarchy).

- **URL**: https://github.com/todotxt/todo.txt

---

## F. BDD and executable specifications

### Cucumber / Gherkin

Given/When/Then syntax that is both human-readable and machine-executable. Steps map to code. Scenarios serve as living documentation. 66% BDD adoption rate per 2025 State of Continuous Testing Report. AI tools now generate Gherkin from requirements.

- **URL**: https://cucumber.io/docs/gherkin/

### Gauge (ThoughtWorks)

Specs written in markdown (`.spec` files) with executable steps. Separates specification from implementation. `--validate` checks parse and implementation errors.

- **URL**: https://docs.gauge.org/

---

## G. Schema references from existing PM tools

### Jira data model

De facto industry standard for work item schemas. Typed fields (summary, description, status, priority, resolution, assignee, labels, components, fix versions, custom fields). Workflow state machines. Link types (blocks, is-blocked-by, duplicates). Dynamic per project + issue type.

- **API docs**: https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-fields/

### Linear GraphQL schema

Strongly typed, published on GitHub. Fields explicitly typed, nullable/non-nullable, relationships first-class. Cleaner reference than Jira.

- **Schema**: https://github.com/linear/linear/blob/master/packages/sdk/src/schema.graphql

### OpenProject

Open-source PM with schema-aware API. Work package schema endpoint returns field names, types, constraints, and allowed values per project+type.

- **URL**: https://www.openproject.org/docs/api/

---

## H. Standards

No IETF RFCs or W3C standards exist for expressing tasks/issues in structured formats. The closest:

- **iCalendar VTODO (RFC 5545)**: Defines status, priority, due date, percent-complete. Calendar-oriented, not rich enough for software task management.
- **JSON Schema**: Used by GitHub Actions, Jira, etc. for field validation. The practical standard for "validate this structured data."
- **OpenAPI**: Defines API schemas that PM tools implement.

---

## Analysis and recommendations

### What the Dagger-drops-CUE lesson tells us

Dagger adopted CUE as its configuration language, then dropped it because developers preferred writing in languages they already know. The lesson: a thin validation layer over familiar formats (YAML, TOML, markdown) beats a new language, no matter how elegant.

### Patterns worth stealing

| Pattern | Source | What to take |
|---|---|---|
| Status as enum with defined transitions | Taskwarrior, Claude Code tasks | Status field must be one of N values; transitions are directional |
| Dependencies as validated references | GitHub Actions `needs`, Taskwarrior UUIDs | Dependency targets must exist; linter rejects dangling refs |
| Phase gates | Spec Kit, Kiro | Cannot proceed to implementation without completed plan |
| Delta specs | OpenSpec | Describe what's changing, not everything |
| Structured acceptance criteria | Gherkin Given/When/Then, Kiro | Machine-parseable "done when" |
| MCP server for agent access | Shrimp, org-mcp | Expose the task graph to agents via protocol |
| YAML workflow blueprints | BMAD Method | Typed task sequences with handoff points |

### If we build something: proposed architecture

```
task files (YAML/TOML)          # human-editable, version-controlled
        │
        ▼
JSON Schema / CUE schema        # defines enums, required fields, ref constraints
        │
        ▼
linter (CI step)                 # validates all task files against schema
        │
        ▼
MCP server (optional)            # exposes task graph to AI agents at runtime
```

**Format choice**: YAML is the pragmatic pick. Everyone knows it, every tool reads it, schema validation is well-supported. TOML is more pleasant to write but has weaker schema tooling. JSON is too noisy for human editing.

**Schema choice**: JSON Schema is the pragmatic pick. CUE/KCL are more powerful but add a learning curve and toolchain dependency. JSON Schema validators exist in every language, IDEs provide completions, and it's the lingua franca of structured data validation.

**What a task file might look like**:

```yaml
id: t1
title: Add linting and type checking to CI
status: plan-needed  # enum: blocked, design-needed, plan-needed, ready, done
depends_on:
  - id: t2
    type: hard        # enum: hard, soft
    reason: "uses --registry paths from T2"
blocked_by: null       # or: "Unity client not ready"
detail_file: t1-linting-ci.md
done_when:
  verifiable_now:
    - "CI workflow file exists at .github/workflows/lint.yml"
    - "`ruff check .` passes in GitHub Actions"
    - "`basedpyright` passes in GitHub Actions"
  requires_infra:
    - "Test PR triggers workflow and passes"
```

**What a schema (JSON Schema) might look like**:

```json
{
  "properties": {
    "status": {
      "enum": ["blocked", "design-needed", "plan-needed", "ready", "done"]
    },
    "depends_on": {
      "items": {
        "properties": {
          "id": { "type": "string", "pattern": "^t\\d+$" },
          "type": { "enum": ["hard", "soft"] }
        }
      }
    }
  }
}
```

A custom linter (Python script, run in CI) would go beyond JSON Schema to validate referential integrity: every `depends_on.id` must match an existing task file.

### Recommended next steps

1. **Immediate (this plan)**: Finish the markdown-based improvements. They're valuable regardless of future tooling.
2. **Study further**: GitHub Spec Kit and BMAD Method are the most worth reading in detail. Shrimp Task Manager is worth trying as an MCP server.
3. **Prototype later**: If the markdown system feels limiting after working through several tickets, build a minimal YAML + JSON Schema + linter prototype. Start with just status enum validation and dependency reference checking. Add complexity only when the simple version proves insufficient.
