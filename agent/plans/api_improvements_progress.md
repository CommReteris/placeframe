# API Improvements — Implementation Progress

Status as of session interruption (Docker nested container fix required).

## Completed

### 1. pytest dependencies
- Added `pytest>=8.0.0` and `pytest-asyncio>=0.24.0` to root `pyproject.toml` dev group
- `uv sync` completed successfully

### 2. PostGIS setup
- `compose.yml`: Changed postgres `x-image-ref` to `docker.io/postgis/postgis:16-3.4-alpine`
- `database/00_extensions.sql`: Added `CREATE EXTENSION IF NOT EXISTS "postgis"`
- `docker/database-manager/src/sql/configure_database.template.sql`: Added `CREATE EXTENSION IF NOT EXISTS "postgis" WITH SCHEMA public`
- `.env.lock`: Updated automatically via `uv run build --lock-only` (new feature, see below)

### 3. Schema changes
- `database/42_nodes.sql`: Made 8 columns nullable (`name`, `label_type`, `label`, `label_scale`, `label_width`, `label_height`, `link_type`, `link`)
- `database/22_localization_maps.sql`: Added GiST index `idx_localization_maps_position_gist`
- `database/42_nodes.sql`: Added GiST index `idx_nodes_position_gist`

### 4. Enhanced localization metrics
- `packages/python/core/src/core/localization_metrics.py`: Added 4 new fields (`num_inliers`, `num_correspondences`, `num_matches`, `inlier_coverage`)
- `docker/localizer/src/build_metrics.py`: Rewritten to compute new metrics including `inlier_coverage` via `scipy.spatial.ConvexHull`
- `docker/localizer/src/localize.py`: Added `num_matches` computation from `match_indices`, passes `num_matches`, `width`, `height` to `build_localization_metrics`

### 5. API spatial query endpoints
- `docker/api/src/routers/spatial.py`: **New file** — shared `validate_spatial_params()` and `apply_spatial_filter()` helpers
- `docker/api/src/routers/localization_maps.py`: Added spatial query params to `fetch_localization_maps` and `get_localization_maps`, uses shared helpers
- `docker/api/src/routers/nodes.py`: Added spatial query params to `get_nodes`, uses shared helpers

### 6. build.py improvements
- Added `--lock-only` flag: updates lock file without building images
- Added stale ref detection: re-resolves image digest when `x-image-ref` in compose.yml differs from lock file
- Skips GC limit check and GPU detection when `--lock-only` is passed

### 7. CLAUDE.md updated
- Added documentation about the generation pipeline (generate-datamodels needs live DB, generate-clients doesn't)

### 8. setup.sh updated
- Added step 9: pins `containerd.io=1.7.28-1` in COI image to fix runc 1.3.3 nested Docker sysctl bug

## Remaining

### Must do next (in order):
1. **Start postgres**: `docker compose --env-file .env --env-file .env.lock up -d postgres`
2. **Run create-database + migrate-database**: Apply schema changes (PostGIS extension + nullable columns + GiST indexes)
3. **Generate datamodels**: `uv run generate-datamodels` (needs live postgres)
4. **Generate clients**: `uv run generate-clients --config openapi-projects.json` (dumps OpenAPI spec from Litestar app, then generates typed Python + C# clients)
5. **Write tests** using the regenerated typed clients:
   - `docker/localizer/tests/test_build_metrics.py` — unit tests for new metrics computation
   - `docker/api/tests/test_spatial_queries.py` — validation logic tests
   - `docker/api/tests/test_nodes.py` — nullable node DTO tests
6. **Run tests**: `uv run pytest`
7. **Unity client update**: `VisualPositioningSystem.cs` — replace rejection logic with direct metric checks using named constants
8. **Lint/typecheck**: `uv run ruff check .` / `uv run ruff format .` / `uv run basedpyright`

### Reference
- Full plan: `agent/plans/api_improvements.md`
