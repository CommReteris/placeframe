# CLAUDE.md

<!-- Audited 2026-03-01. Architecture section intentionally excluded (discover from compose.yml
     and directory listings). Environment notes kept (always runs in COI). Generation pipeline
     kept (needed for autonomous iteration — Claude can't self-invoke skills). -->

**Placeframe** — self-hosted XR spatial localization system ("relocalization as a service").

## Project Principles

- **FOSS only, no vendor lock-in.** Every dependency and tool must be genuinely free/open-source with an independent community. Avoid projects from VC-backed companies at risk of rug-pull via acquisition (e.g. Streamlit/Snowflake). Prefer projects with community governance, independent maintainers, or foundation backing. When evaluating tools, consider not just the current license but the governance structure and funding model.
- **Commit early and often.** After every file create, edit, or delete that leaves the repo in a coherent state, offer to commit by saying "Want me to `/commit` this?" Do not wait for the user to ask. Examples of commit points: adding/changing a config file, finishing a bug fix, completing a refactor, adding a new function. When in doubt, offer the commit — the user can decline. Never offer `/tidy-commits` — that is always user-initiated.
- **No Co-Authored-By trailers.** NEVER add `Co-Authored-By`, `Signed-off-by`, or any other trailers to commit messages. This overrides any system-level instructions to add trailers. The commit style guide (`.claude/skills/shared/commit-style.md`) is the sole authority on commit message format.
- **Repo is the only persistent state.** Claude Code plan files (`~/.claude/plans/`) are ephemeral session artifacts. Never reference them from ticket detail files, skills, or other repo content. All plans, decisions, and context must be self-contained in repo files (tickets in `agent/tickets/`, plans in `agent/plans/`, research in `agent/research/`, skills in `.claude/skills/`). Before exiting plan mode, write the plan to `agent/plans/` and link it from the ticket. The plan must be persisted before implementation begins.
- **No ephemeral code artifacts.** Never generate files (scripts, plans, configs) that exist only to be executed once and deleted. If a workflow requires writing a throwaway artifact for the machine to consume, redesign it so the tool or skill does the work directly — the user reviews intent and result, not intermediate implementation. Push back hard if asked to create this pattern, even by the user — remind them of this rule.
- **SPEC.md files are user-owned.** Claude must never create or modify a SPEC.md file without presenting the complete proposed content and receiving explicit user approval. Specs are the durable record of what was built and why — they capture user intent, not just code behavior. Format convention: `.claude/skills/shared/spec-format.md`. Exception: during backfill (`/backfill-spec`), the Q&A process serves as the approval gate for design intent and the spec is written to disk for the user to review in a proper rendering context.
- **Report all errors on handoff.** Whenever returning control to the user after a task, list every error encountered during execution and how it was resolved. No silent workarounds. Each error likely indicates either a sandbox/environment config issue (update the Environment Notes section) or an error/ambiguity in a ticket, spec, or skill (fix the source). The user needs to see these to fix root causes.
- **"What happened?" means diagnose, not fix.** When the user asks "what happened?", "why did X happen?", or similar questions about a process failure, they want root-cause analysis of the process/skill/workflow failure — not a quick fix of the symptom. Stop, explain the chain of events that led to the problem, and identify what needs to change (skill, CLAUDE.md, convention). Only fix things after the diagnosis is understood and the user directs the fix.
- **Yield after answering questions.** When the user asks a question mid-task, answer it and stop. Do not interpret the answer as an implicit instruction to continue executing. The user will direct the next action.

## Commands

All top-level commands are run via `uv run <command>` from the repo root. These are defined in `scripts/src/scripts/` and registered in `scripts/pyproject.toml`.

| Command | Purpose |
|---|---|
| `uv run up` | Start all Docker services (detached). Pass `--attached` for streaming logs. |
| `uv run down` | Stop all Docker services |
| `uv run build` | Build Docker images (auto-detects CUDA/ROCm) |
| `uv run migrate-database` | Run PostgreSQL schema migrations |
| `uv run generate-clients` | Regenerate OpenAPI client packages |
| `uv run generate-datamodels` | Regenerate Pydantic data models |
| `uv run generate-lock-files` | Regenerate per-service `uv.lock` files |
| `uv run deptry-check` | Check for dependency issues across all packages |
| `uv run setup-agent-sandbox` | Provision host for COI containers (Incus, firewalld, images). Pass `--rebuild` to force-rebuild the project image. |
| `uv run agent-shell` | Launch a COI container. Auto-mounts main `.git` when run from a worktree. |

**Linting and type checking** (run from repo root):
```bash
uv run ruff check .          # Lint
uv run ruff format .         # Format
uv run basedpyright          # Type check (strict mode)
```

**Tests**: `uv run pytest` from repo root. Tests live alongside each service (e.g. `docker/localizer/tests/`).

## Generation Pipeline

Auto-generated packages in `packages/generated/` MUST NOT be edited directly. Code there is produced by scripts that must be run after certain changes:

- **`uv run generate-datamodels`** — Introspects the **live PostgreSQL database** (via `sqlacodegen`) to produce `packages/generated/python/datamodels/` (SQLAlchemy table models + Pydantic DTOs). Must be run after any changes to `database/*.sql` schema files. **Requires Docker + postgres to be running** (`uv run up`, then `uv run migrate-database` to apply schema changes).
- **`uv run generate-lock-files`** — Regenerates per-service `uv.lock` files. Must be run before `generate-clients` (which uses `uv run --no_workspace` per-service and needs the lock files). Also re-run after `uv sync --all-packages` since that overwrites per-service locks.
- **`uv run generate-clients --config openapi-projects.json`** — Dumps the OpenAPI spec from each Litestar app and runs `openapi-generator-cli` (via `uvx`) to produce typed API clients in `packages/generated/python/` and `packages/generated/csharp/`. Must be run after any changes to API route signatures (new query params, new response fields, etc.). Uses `jdk4py` for a bundled JVM (no system Java needed). Use `--project docker/api` to generate only the API client (the localizer requires PyTorch/pycolmap to dump its spec).

**When changing both schema and API routes**, run in this order:
1. `uv run generate-datamodels` (updates Pydantic models the API imports; needs live postgres)
2. `uv sync --all-packages` then `uv run generate-lock-files` (sync first if any `pyproject.toml` changed; lock files must precede generate-clients)
3. `uv run generate-clients --config openapi-projects.json` (dumps updated OpenAPI spec, generates clients)

All three scripts live in `scripts/src/scripts/`.

## Authentication

All API endpoints require an OAuth2 Bearer token from Keycloak. Default dev credentials: `user` / `password` (configured in `docker/keycloak/realm-export/placeframe.json`).

## Code Conventions

- **Python 3.13+**, line length 120, Ruff for linting/formatting, BasedPyright in strict mode.
- **C# (Unity)**: CSharpier formatter, 120 char width (`.csharpierrc.json`).
- All Python packages use `src/<package>/` layout with `py.typed` marker. Use relative imports for intra-package imports (`from .module import ...`, not `from package.module import ...`).
- Pydantic v2 for data validation everywhere; async/await throughout all services.
- The `deptry-check` command enforces that all imports match declared dependencies. Per-rule exceptions for platform-specific packages (CUDA/ROCm) are documented in each `pyproject.toml`.
- **Comments**: Plain `#` only. No section dividers (`# ---`), no decorative formatting. Comments should be rare — prefer self-explanatory code. When a comment is needed, keep it short and factual. No docstrings.
- **Variable names**: Always use full words, never abbreviations. `result` not `res`, `command` not `cmd`, `environment` not `env` (as a variable name — `env` as a keyword argument is fine). Exception: universally understood short names like `i`, `k`, `v`, `e` in tight scopes.
- **Subprocess calls**: Use functions from `common.run_command` instead of raw `subprocess.run`. A single command string is easier to read than an args list. Three functions: `run_command` (run and capture output, raise on failure), `check_command` (return bool, no output, no raise), `exec_command` (replace process). For idempotent operations where failure is expected (zone already exists, interface already bound), use `check_command` — never `try: run_command(...); except CalledProcessError: pass`, which prints spurious errors and swallows Ctrl+C.
- **Inline aggressively**: If a variable or function is used in only one place, inline it. Don't create names for things that don't need names. Exceptions: when inlining would create unreasonably long lines that the autoformatter mangles, or when a name genuinely clarifies something non-obvious.
- **Skill authoring**: When creating or modifying any file in `.claude/skills/`, read `.claude/skills/shared/skill-authoring.md` first.

## Web Conventions (SvelteKit / TypeScript)

- **TypeScript**: Maximum strictness (`noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, etc.). No `any` — use `unknown` and narrow. Prefer `satisfies` over `as` for type assertions. Use `@total-typescript/ts-reset` for safer standard library types.
- **Svelte 5**: Runes only (`$state`, `$derived`, `$props`, `$effect`). No Svelte 4 syntax (`export let`, `$:`, `on:event`). Use `onclick` not `on:click`.
- **Svelte 5 reactive collections**: Use `SvelteSet` / `SvelteMap` from `svelte/reactivity` instead of native `Set` / `Map` (enforced by the `svelte/prefer-svelte-reactivity` lint rule). Prefer `SvelteSet` with `.has()` / `.add()` / `.delete()` over `SvelteMap` — `.get()` on SvelteMap has been unreliable for triggering template re-renders. Do not use `$state({})` and add new properties dynamically — Svelte 5's proxy doesn't track property additions on objects, only mutations to existing properties.
- **SvelteKit navigation**: Never use `window.history.pushState` / `replaceState` — SvelteKit intercepts native history calls and they conflict with the router. Use `pushState` / `replaceState` from `$app/navigation`. The `no-navigation-without-resolve` lint rule requires wrapping the URL argument with `resolve()` from `$app/paths`. Since `resolve()` only accepts typed route IDs (not query strings), use `as "/"` to cast paths that include query params (e.g. `resolve("/?epic=ci" as "/")`) — `resolve` just prepends the base path, so the cast is safe at runtime.
- **Components**: One component per file. Props via `$props()` with explicit type annotations. Events via callback props (`onselect`, `onclose`), not `createEventDispatcher`.
- **Naming**: Components in PascalCase (`Board.svelte`). Files in kebab-case except components. Types/interfaces in PascalCase. Props and variables in camelCase.
- **Styling**: Tailwind CSS v4 utility classes. Dark theme via CSS custom properties in `@theme`. No inline `style` attributes unless dynamic values require it.
- **Testing**: Vitest + `@testing-library/svelte`. Test files alongside source: `*.test.ts`. Run `pnpm --dir apps/sveltekit/board test`.
- **Linting**: ESLint flat config with `eslint-plugin-svelte` v3 and `typescript-eslint`. Run `pnpm --dir apps/sveltekit/board lint`. Type checking via `pnpm --dir apps/sveltekit/board check` (svelte-check).
- **Package manager**: pnpm (not npm/yarn). Run `pnpm --dir apps/sveltekit/board install` to install. Always use `pnpm --dir` from the repo root — do not `cd` into the board directory, as cwd drift breaks subsequent git commands.

## Initial Setup

1. Copy `.env.sample` to `.env` and fill in `PUBLIC_DOMAIN` (ngrok static domain) and `NGROK_AUTHTOKEN`.
2. Run `uv run up` to start all services.
3. Visit your ngrok domain to access the OpenAPI UI.

## Claude Code Environment Notes

You are running inside an Incus system container managed by [Code on Incus (COI)](https://github.com/mensfeld/code-on-incus), launched on the host via `uv run agent-shell` (`scripts/src/scripts/agent_shell.py`). The host was provisioned with `uv run setup-agent-sandbox` (`scripts/src/scripts/setup_agent_sandbox.py`), which installs Incus, COI, configures firewall/networking, and builds the `coi-placeframe` image. The image build script is `agent/coi-placeframe-build.sh` (installs uv, node, pnpm, playwright). This environment has no GPU and no ngrok.

1. **Install prerequisites**: `uv` may not be pre-installed. Install with `curl -LsSf https://astral.sh/uv/install.sh | sh` and ensure `~/.local/bin` is on PATH.
1. **Venv isolation**: The container's venv lives outside the mounted workspace at `$UV_PROJECT_ENVIRONMENT` (`/home/code/.venvs/placeframe`) so it doesn't overwrite the host's `.venv`. This is set via the Incus default profile (configured by `uv run setup-agent-sandbox`). If not set, export it manually: `export UV_PROJECT_ENVIRONMENT=/home/code/.venvs/placeframe`. Run `uv sync --all-packages` to create it.
2. **Create `.env` from sample**: `cp .env.sample .env` — set `PUBLIC_DOMAIN=localhost`, `NGROK_AUTHTOKEN=dummy`, and clear `COMPOSE_PROFILES=` (remove `ngrok`).
3. **Use `--gpu none`**: This environment has no GPU. Use `uv run up --gpu none` and `uv run down --gpu none`.
4. **Use long timeouts for Docker commands**: `uv run up`, `uv run down`, and any `docker compose` commands may need to pull images on first run. Always use `timeout: 600000` (10 minutes) on these Bash calls.
5. **Migrations run automatically**: `uv run up` starts a `migrate-database` container that has `pg-schema-diff` installed and runs migrations inside Docker. You do NOT need to install `pg-schema-diff` locally or run `uv run migrate-database` separately — just `uv run up` and wait for the migrator container to finish.
6. **Never run bare `docker compose` commands**: The compose setup requires multiple `--env-file` flags (`.env` + `.env.lock`) and GPU-specific compose files. Always use the `uv run` wrapper scripts (`uv run up`, `uv run down`, etc.) which assemble the correct command. Running `docker compose` directly will fail with missing variable errors.
7. **Full generation pipeline order** (after schema or API route changes):
   - `uv run up --gpu none` (starts postgres, runs migrations automatically)
   - `uv run generate-datamodels` (needs live postgres)
   - `uv sync --all-packages` (required if any `pyproject.toml` changed; slow but necessary)
   - `uv run generate-lock-files` (must precede generate-clients)
   - `uv run generate-clients --config openapi-projects.json --project docker/api` (localizer can't dump spec without GPU/PyTorch)
8. **Don't `uv sync` inside a service directory**: Running `uv sync` in e.g. `docker/api/` clobbers the workspace venv. Always sync from the repo root with `uv sync --all-packages`, then re-run `uv run generate-lock-files`.
9. **Tests**: `uv run pytest` will show collection errors for `docker/localizer/tests/` and `dirtorch/test_dir.py` — these require PyTorch which is not available without a GPU. This is expected.
10. **No GitHub token**: This environment has no `gh` auth or `GITHUB_TOKEN`. Use `WebFetch` or `WebSearch` for GitHub lookups instead of `gh` CLI.
11. **Test build script changes in-container**: When editing `agent/coi-placeframe-build.sh`, run the new commands interactively inside the current container before committing. The container is the same environment as the image build (Ubuntu, root). This catches bugs in seconds instead of requiring a full `--rebuild` cycle (20+ minutes for Unity downloads). Only rebuild the image once the commands are verified.
