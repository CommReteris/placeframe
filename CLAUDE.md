# CLAUDE.md

<!-- Agent sandbox and skills infrastructure extracted to Pulsar repo (2026-03-07). -->

**Placeframe** — self-hosted XR spatial localization system ("relocalization as a service").

## Project Principles

- **FOSS only, no vendor lock-in.** Every dependency and tool must be genuinely free/open-source with an independent community. Avoid projects from VC-backed companies at risk of rug-pull via acquisition (e.g. Streamlit/Snowflake). Prefer projects with community governance, independent maintainers, or foundation backing. When evaluating tools, consider not just the current license but the governance structure and funding model.
- **SPEC.md files are user-owned.** Claude must never create or modify a SPEC.md file without presenting the complete proposed content and receiving explicit user approval. Specs are the durable record of what was built and why — they capture user intent, not just code behavior.
- **Report all errors on handoff.** Whenever returning control to the user after a task, list every error encountered during execution and how it was resolved. No silent workarounds. Each error likely indicates either a sandbox/environment config issue (update the Environment Notes section) or an error/ambiguity in a ticket, spec, or skill (fix the source). The user needs to see these to fix root causes.
- **Diagnose first, fix only when asked.** When encountering any failure — CI errors, test failures, runtime exceptions, "what happened?" questions — default to root-cause analysis, not fixing. Present the diagnosis and yield. Only fix after the user directs the fix. This applies whether the user says "what happened?", reports an error, or pastes a failing log.
- **Yield after answering questions.** When the user asks a question mid-task, answer it and stop. Do not interpret the answer as an implicit instruction to continue executing. The user will direct the next action.
- **Never bypass safety checks without asking.** When a tool, linter, or validation rejects an action, do not reach for a `--force`, `--disable-*`, `--no-verify`, or equivalent bypass flag. First: understand why the check exists. Second: look for an alternative that satisfies the check (e.g. use relative paths instead of disabling path validation). Third: if no clean alternative exists, explain the tradeoff and ask the user before applying the bypass.

## Commands

All top-level commands are run via `uv run <command>` from the repo root. These are defined in `scripts/src/scripts/` and `build/src/build_scripts/`, registered in `scripts/pyproject.toml` and `build/pyproject.toml`.

| Command | Purpose |
|---|---|
| `uv run up` | Start all Docker services (detached). Pass `--attached` for streaming logs. |
| `uv run down` | Stop all Docker services |
| `uv run build` | Build Docker images (auto-detects CUDA/ROCm) |
| `uv run migrate-database` | Run PostgreSQL schema migrations |
| `uv run generate-clients` | Regenerate OpenAPI client packages |
| `uv run generate-datamodels` | Regenerate Pydantic data models |
| `uv run lock-python` | Regenerate Python lock files (`uv.lock` + per-service `pylock.*.toml`). `--check` for CI validation. |
| `uv run lock-unity` | Regenerate Unity `packages-lock.json` files. `--check` for CI validation, `--project NAME` to limit scope. |
| `uv run deptry-check` | Check for dependency issues across all packages |

**Linting and type checking** (run from repo root):
```bash
uv run ruff check .          # Lint
uv run ruff format .         # Format
uv run basedpyright          # Type check (strict mode)
```

**Tests**: `uv run pytest` from repo root. Tests live alongside each service (e.g. `docker/localizer/tests/`).

## Generation Pipeline

Packages in `packages/generated/` are hook-protected — edit the source and run the appropriate generator:

- **`uv run generate-datamodels`** — Introspects the **live PostgreSQL database** (via `sqlacodegen`) to produce `packages/generated/python/datamodels/` (SQLAlchemy table models + Pydantic DTOs). Must be run after any changes to `database/*.sql` schema files. **Requires Docker + postgres to be running** (`uv run up`, then `uv run migrate-database` to apply schema changes).
- **`uv run lock-python`** — Regenerates Python lock files: workspace `uv.lock` and per-service `pylock.*.toml` exports. `--check` validates without writing (used in CI). Must be run before `generate-clients` (which uses `uv run --no_workspace` per-service and needs the lock files). Also re-run after `uv sync --all-packages` since that overwrites per-service locks.
- **`uv run lock-unity`** — Regenerates Unity `packages-lock.json` files via batchmode. `--check` validates without writing (used in CI). `--project <name>` to limit to one project.
- **`uv run generate-clients --config build/openapi-projects.json`** — Dumps the OpenAPI spec from each Litestar app and runs `openapi-generator-cli` (via `uvx`) to produce typed API clients in `packages/generated/python/` and `packages/generated/csharp/`. Must be run after any changes to API route signatures (new query params, new response fields, etc.). Uses `jdk4py` for a bundled JVM (no system Java needed). Use `--project docker/api` to generate only the API client (the localizer requires PyTorch/pycolmap to dump its spec).

**When changing both schema and API routes**, run in this order:
1. `uv run generate-datamodels` (updates Pydantic models the API imports; needs live postgres)
2. `uv sync --all-packages` then `uv run lock-python` (sync first if any `pyproject.toml` changed; lock files must precede generate-clients)
3. `uv run generate-clients --config build/openapi-projects.json` (dumps updated OpenAPI spec, generates clients)

Generation scripts live in `scripts/src/scripts/` (`generate-datamodels`, `generate-clients`) and `build/src/build_scripts/` (`lock-python`, `lock-unity`).

## Authentication

All API endpoints require an OAuth2 Bearer token from Keycloak. Default dev credentials: `user` / `password` (configured in `docker/keycloak/realm-export/placeframe.json`).

## CI/CD

CI runs in a single unified workflow (`.github/workflows/ci.yml`) with two build paths — Docker and Unity — gated by a shared preflight job. Build logic lives in `scripts/src/scripts/build.py` (Docker) and `build/src/build_scripts/` (Unity).

- **Triggers**: pushes to long-running branches (`main`, `dev`) and PRs targeting them. `paths-ignore: [".env.lock"]` prevents loops.
- **Job graph**: `preflight` (static analysis, codegen staleness), `activate-license`, and `matrix` start in parallel. `build-docker` runs after preflight. `unity-preflight` (Unity lock check) runs after preflight + license activation. `build-unity` matrix runs after all Unity prerequisites.
- **Lock file flow**: CI builds images, then commits `.env.lock` (pinned image digests) directly to the branch. No lock PR — the old `peter-evans/create-pull-request` approach is gone.
- **Branch protection** (configured in GitHub repo settings, not in code): require PRs, require status checks (`build-docker`), and **require branches to be up to date before merging**. The "up to date" requirement is the key mechanism — it ensures PRs are rebased before merge, so `.env.lock` is already correct when the PR lands.
- **Developer setup**: run `git config merge.ours.driver true` once per clone. This enables the `merge=ours` strategy in `.gitattributes` for `.env.lock`, which is a safety net for local command-line merges.
- **Adding a new long-running branch**: update `branches` lists in `ci.yml` (3 places: `push.branches`, `pull_request.branches`, and the `contains()` check in the commit step's `if` condition).
- **Unity Library cache**: cached via ORAS, keyed by project name + platform + branch. The cache is treated as a warm-start for incremental builds — Unity reimports changed assets automatically, so a stale Library is always better than no Library.

## R3 Reactive Library (C#/Unity)

This project uses **R3** (Cysharp/R3), not RxNET/ReactiveX. R3 has fundamentally different error semantics:

- **Exceptions in Subscribe/SubscribeAwait callbacks do NOT kill the subscription.** R3 catches the exception, routes it to `OnErrorResume` (non-terminal), and the subscription continues processing future emissions. This is the opposite of traditional Rx, where `OnError` is terminal and disposes the subscription.
- **`ObservableSystem.RegisterUnhandledExceptionHandler`** is the global fallback. When no per-subscription `onErrorResume` handler is provided, exceptions route here. The subscription still survives.
- **To opt into terminal error behavior** (traditional Rx semantics), you must explicitly add `.OnErrorResumeAsFailure()` before subscribing. This project does not use that operator.
- **Do not "fix" R3 subscriptions by converting throws to early returns** just because a callback throws. The throw may be intentional — R3 is designed so that transient failures don't kill long-running subscriptions. Instead, evaluate whether the exception represents a bug, a normal operational outcome that should be logged at a lower level, or a condition that genuinely should stop the subscription.

## Code Conventions

- **Python 3.13+**, line length 120, Ruff for linting/formatting, BasedPyright in strict mode.
- **C# (Unity)**: CSharpier formatter, 120 char width (`.csharpierrc.json`). `.meta` files are hook-protected — Unity generates them on asset import. Hand-written `.meta` files risk incorrect GUIDs, wrong import settings, and subtle asset reference bugs. If a `.meta` file needs different settings (e.g. PluginImporter platform targeting), use Unity batchmode to reimport the asset. `packages-lock.json` files are also hook-protected — Unity generates them during package resolution. To update them, run Unity batchmode and let it re-resolve. **If Unity batchmode changes `packages-lock.json` unexpectedly, do not ignore it.** Either the lock was stale (a prior change to `manifest.json` or a local package's `package.json` wasn't followed by a lock regeneration) or something is wrong with the environment (missing registry access, wrong package versions). Investigate the cause: check `git log` for the lock file and the package sources it depends on, identify the commit that desynchronized them, and commit the regenerated lock if it reflects the correct state.
- All Python packages use `src/<package>/` layout with `py.typed` marker. Use relative imports for intra-package imports (`from .module import ...`, not `from package.module import ...`).
- Pydantic v2 for data validation everywhere; async/await throughout all services.
- The `deptry-check` command enforces that all imports match declared dependencies. Per-rule exceptions for platform-specific packages (CUDA/ROCm) are documented in each `pyproject.toml`.
- **Comments**: Plain `#` only. No section dividers (`# ---`), no decorative formatting. Comments should be rare — prefer self-explanatory code. When a comment is needed, keep it short and factual.
- **No docstrings.** Do not add docstrings to functions, classes, or modules — no exceptions.
- **Variable names**: Always use full words, never abbreviations. `result` not `res`, `command` not `cmd`, `environment` not `env` (as a variable name — `env` as a keyword argument is fine). Exception: universally understood short names like `i`, `k`, `v`, `e` in tight scopes.
- **Subprocess calls**: Use functions from `common.run_command` instead of raw `subprocess.run`. A single command string is easier to read than an args list. Three functions: `run_command` (run and capture output, raise on failure), `check_command` (return bool, no output, no raise), `exec_command` (replace process). For idempotent operations where failure is expected (zone already exists, interface already bound), use `check_command` — never `try: run_command(...); except CalledProcessError: pass`, which prints spurious errors and swallows Ctrl+C.
- **Typer entry points**: Scripts using `typer.Typer()` with `@app.command()` must use `:app` as the entry point in `pyproject.toml`, not `:main`. Calling `:main` bypasses typer's CLI argument parsing. Scripts that don't use typer (plain functions) use `:main` as normal.
- **Inline aggressively**: If a variable or function is used in only one place, inline it. Don't create names for things that don't need names. Exceptions: when inlining would create unreasonably long lines that the autoformatter mangles, or when a name genuinely clarifies something non-obvious.
- **Never autosquash pushed commits.** `git commit --fixup` + `git rebase --autosquash` rewrites commit SHAs. If the original commits have already been pushed, the rebase creates divergence that requires a force push to resolve. Only use `--fixup`/`--autosquash` on commits that are local-only. For already-pushed commits, make the fix as a new commit.

## Environment

- **Unity**: Available at `/opt/unity/6000.0.66f1/Editor/Unity`. Use for batchmode operations (package lock regeneration, asset import, player builds). Matches the Unity version used in CI (`unityci/editor:6000.0.66f1`).
- **GitHub token is read-only.** The `gh` CLI can read repos, list runs, and view logs, but cannot push commits or trigger workflow dispatches. Always ask the user to push and trigger workflows from their host.

## Initial Setup

1. Copy `.env.sample` to `.env` and fill in `PUBLIC_DOMAIN` (ngrok static domain) and `NGROK_AUTHTOKEN`.
2. Run `uv run up` to start all services.
3. Visit your ngrok domain to access the OpenAPI UI.
