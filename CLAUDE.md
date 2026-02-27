# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

**Placeframe** is a self-hosted XR spatial localization system ("relocalization as a service"). It determines an XR device's position and rotation relative to a canonical reference frame for a physical space — an open-source alternative to Apple Shared World Anchors, Google ARCore Cloud Anchors, etc.

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

There is no test runner configured — no test suite exists yet.

## Architecture

The system runs as a set of Docker microservices defined in `compose.yml`, with GPU overrides in `compose.cuda.yml` and `compose.rocm.yml`.

### Core Services

| Service | Path | Technology | Role |
|---|---|---|---|
| `api` | `docker/api/` | Litestar (ASGI) | Main REST API: manages users, places, captures, maps |
| `localizer` | `docker/localizer/` | Litestar (ASGI) | Runs image-to-map localization (LightGlue feature matching + RANSAC) |
| `reconstructor` | `docker/reconstructor/` | Python + pycolmap | Builds 3D maps from capture sessions |
| `state-sync` | `docker/orchestrator/` | Python worker | Polls the database and orchestrates async jobs between services |
| `database-manager` | `docker/database-manager/` | Python | Runs SQL migrations at startup |
| `auth-initializer` | `docker/auth-initializer/` | Python | Configures Keycloak realm on startup |
| `gateway` | `docker/gateway/` | ngrok | Public HTTPS tunnel |
| `keycloak` | `docker/keycloak/` | Keycloak 26 | OpenID Connect / OAuth2 identity provider |

**Backing services**: PostgreSQL 16, MinIO (S3-compatible object storage), CloudBeaver (database UI).

### Python Workspace

The repo is a `uv` monorepo. Shared Python code lives in `packages/python/`:

- **`common`** — utilities for boto/MinIO, Docker SDK, Litestar, JWT
- **`core`** — domain logic: camera configs, coordinate transforms, metrics
- **`neural-networks`** — PyTorch models with conditional extras (`cpu`, `cuda`, `rocm`)
- **`datamodels`** — auto-generated Pydantic models from the OpenAPI schema
- **`api-client` / `localizer-client`** — auto-generated async API clients

Auto-generated packages in `packages/generated/` should not be edited directly — regenerate them with the commands above.

**Generation pipeline**: Code in `packages/generated/` is produced by two scripts that must be run after certain changes:

- **`uv run generate-datamodels`** — Introspects the **live PostgreSQL database** (via `sqlacodegen`) to produce `packages/generated/python/datamodels/` (SQLAlchemy table models + Pydantic DTOs). Must be run after any changes to `database/*.sql` schema files. **Requires Docker + postgres to be running** (`uv run up`, then `uv run migrate-database` to apply schema changes).
- **`uv run generate-clients`** — Dumps the OpenAPI spec from the Litestar app (no database needed) and runs `openapi-generator-cli` to produce typed API clients in `packages/generated/python/` and `packages/generated/csharp/`. Must be run after any changes to API route signatures (new query params, new response fields, etc.).

**When changing both schema and API routes**: run `generate-datamodels` first (it updates the Pydantic models the API imports), then `generate-clients` (it dumps the updated OpenAPI spec). Both scripts live in `scripts/src/scripts/`.

### Data Flow

1. **Capture**: Unity mobile app (ARFoundation, C#) records images + sensor data and POSTs to the API.
2. **Reconstruction**: The `state-sync` worker triggers the `reconstructor`, which uses pycolmap to build a sparse 3D map (point cloud + camera poses). The result is stored in MinIO.
3. **Localization**: A Unity client sends a query image to the `localizer`, which matches it against a stored map using LightGlue feature matching, then estimates 6-DOF pose via RANSAC/PnP.
4. **Georeferencing**: The Map Registration Tool (Unity standalone) can visually align point clouds against Cesium tilesets (OSM / Google Photorealistic Tiles).

### Authentication

All API endpoints require an OAuth2 Bearer token from Keycloak. The default dev credentials are `user` / `password` (configured in `docker/keycloak/realm-export/placeframe.json`). The `state-sync` worker uses client credentials to authenticate service-to-service calls.

## Code Conventions

- **Python 3.13+**, line length 120, Ruff for linting/formatting, BasedPyright in strict mode.
- **C# (Unity)**: CSharpier formatter, 120 char width (`.csharpierrc.json`).
- All Python packages use `src/<package>/` layout with `py.typed` marker.
- Pydantic v2 for data validation everywhere; async/await throughout all services.
- The `deptry-check` command enforces that all imports match declared dependencies. Per-rule exceptions for platform-specific packages (CUDA/ROCm) are documented in each `pyproject.toml`.

## Initial Setup

1. Copy `.env.sample` to `.env` and fill in `PUBLIC_DOMAIN` (ngrok static domain) and `NGROK_AUTHTOKEN`.
2. Run `uv run up` to start all services.
3. Visit your ngrok domain to access the OpenAPI UI.
