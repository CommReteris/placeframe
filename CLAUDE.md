# CLAUDE.md

<!-- Audited 2026-03-01. Architecture section intentionally excluded (discover from compose.yml
     and directory listings). Environment notes kept (always runs in COI). Generation pipeline
     kept (needed for autonomous iteration — Claude can't self-invoke skills). -->

**Placeframe** — self-hosted XR spatial localization system ("relocalization as a service").

## Project Principles

- **FOSS only, no vendor lock-in.** Every dependency and tool must be genuinely free/open-source with an independent community. Avoid projects from VC-backed companies at risk of rug-pull via acquisition (e.g. Streamlit/Snowflake). Prefer projects with community governance, independent maintainers, or foundation backing. When evaluating tools, consider not just the current license but the governance structure and funding model.
- **Commit early and often.** After every file create, edit, or delete that leaves the repo in a coherent state, offer to commit by saying "Want me to `/commit` this?" Do not wait for the user to ask. Examples of commit points: adding/changing a config file, finishing a bug fix, completing a refactor, adding a new function. When in doubt, offer the commit — the user can decline.
- **Repo is the only persistent state.** Claude Code plan files (`~/.claude/plans/`) are ephemeral session artifacts. Never reference them from ticket detail files, skills, or other repo content. All plans, decisions, and context must be self-contained in repo files (ticket detail files in `agent/plans/`, research in `agent/research/`, skills in `.claude/skills/`).

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
- All Python packages use `src/<package>/` layout with `py.typed` marker.
- Pydantic v2 for data validation everywhere; async/await throughout all services.
- The `deptry-check` command enforces that all imports match declared dependencies. Per-rule exceptions for platform-specific packages (CUDA/ROCm) are documented in each `pyproject.toml`.
- **Comments**: Plain `#` only. No section dividers (`# ---`), no decorative formatting. Comments should be rare — prefer self-explanatory code. When a comment is needed, keep it short and factual. No docstrings.
- **Variable names**: Always use full words, never abbreviations. `result` not `res`, `command` not `cmd`, `environment` not `env` (as a variable name — `env` as a keyword argument is fine). Exception: universally understood short names like `i`, `k`, `v`, `e` in tight scopes.
- **Subprocess calls**: Use `run_command` or `exec_command` from `common.run_command` instead of raw `subprocess.run`. A single command string is easier to read than an args list.
- **Inline aggressively**: If a variable or function is used in only one place, inline it. Don't create names for things that don't need names. Exceptions: when inlining would create unreasonably long lines that the autoformatter mangles, or when a name genuinely clarifies something non-obvious.

## Initial Setup

1. Copy `.env.sample` to `.env` and fill in `PUBLIC_DOMAIN` (ngrok static domain) and `NGROK_AUTHTOKEN`.
2. Run `uv run up` to start all services.
3. Visit your ngrok domain to access the OpenAPI UI.

## Claude Code Environment Notes

When running in a containerized Claude Code environment (no GPU, no ngrok):

1. **Install prerequisites**: `uv` may not be pre-installed. Install with `curl -LsSf https://astral.sh/uv/install.sh | sh` and ensure `~/.local/bin` is on PATH. Java (JDK 11+) is required for `generate-clients` — install with `sudo apt-get install -y default-jre-headless`.
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
