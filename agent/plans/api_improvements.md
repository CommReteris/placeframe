# Plan: Spatial Queries, Optional Node Fields, Enhanced Localization Metrics

## Context

Three improvements to Placeframe:

1. **Spatial radius queries** — Clients need to discover maps and nodes near a geographic position. Currently the only filters are by ID. Positions are ECEF Cartesian coordinates.
2. **Optional node fields** — Node `name`, `label`/`label_*`, and `link`/`link_type` are currently all NOT NULL. They should be nullable so nodes can be created without content metadata.
3. **Better localization metrics** — Only `inlier_ratio` and `reprojection_error_median` are exposed. The client needs richer metrics for (a) rejection of bad localizations and (b) telemetry to evaluate mapping strategies. The current rejection logic in `VisualPositioningSystem.cs` uses a counterintuitive "low reprojection error = too few inliers" proxy that should be replaced with direct metrics.

---

## 1. Spatial Radius Query Endpoints

**Approach:** PostGIS with functional GiST indexes on existing columns. No geometry columns or GeoAlchemy2 needed — we use `ST_MakePoint()` expressions that PostgreSQL indexes and queries against directly. This gives full spatial index performance at scale while keeping the existing schema structure intact.

**Files to modify:**

- `.env.lock` — change `POSTGRES_IMAGE` from `postgres:16-alpine` to `postgis/postgis:16-3.4-alpine`
- `docker/database-manager/src/sql/configure_database.template.sql` — add `CREATE EXTENSION IF NOT EXISTS postgis` (actually creates extension)
- `database/00_extensions.sql` — add `CREATE EXTENSION IF NOT EXISTS postgis` (desired state for pg-schema-diff)
- `database/22_localization_maps.sql` — add functional GiST index
- `database/42_nodes.sql` — add functional GiST index
- `docker/api/src/routers/localization_maps.py` — add spatial filter to GET endpoint
- `docker/api/src/routers/nodes.py` — add spatial filter to GET endpoint

**Database changes:**

Extensions are created in two places (matching the existing `uuid-ossp` pattern):

1. `docker/database-manager/src/sql/configure_database.template.sql` — add after the existing `uuid-ossp` line (line 7). This is where the extension is actually created during database setup, before pg-schema-diff runs.
2. `database/00_extensions.sql` — add as desired state so pg-schema-diff doesn't see a diff.

Both get:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

Add functional GiST indexes (to each table's SQL file):

```sql
CREATE INDEX idx_localization_maps_position_gist ON localization_maps
  USING GIST (ST_MakePoint(position_x, position_y, position_z));

CREATE INDEX idx_nodes_position_gist ON nodes
  USING GIST (ST_MakePoint(position_x, position_y, position_z));
```

These store precomputed geometry values in a GiST R-tree at insert/update time. Queries using the same `ST_MakePoint(...)` expression hit the index directly — same performance as indexing a stored geometry column.

**API implementation:**

Add optional query params `position_x`, `position_y`, `position_z`, `radius` (all `float | None`) to both GET endpoints. Validate all-or-none. Use PostGIS `ST_3DDWithin` via SQLAlchemy's generic `func`:

```python
from sqlalchemy import func

query = query.where(
    func.ST_3DDWithin(
        func.ST_MakePoint(Model.position_x, Model.position_y, Model.position_z),
        func.ST_MakePoint(position_x, position_y, position_z),
        radius,
    )
)
```

No GeoAlchemy2 dependency needed — SQLAlchemy's `func` generates arbitrary SQL function calls.

For localization maps: add params to both `get_localization_maps` and `fetch_localization_maps` (since `fetch_localization_maps` is reused by the localization router). Spatial filter is mutually exclusive with `ids` and `reconstruction_ids` — extend the existing validation pattern at line 80-81.

For nodes: add params to `get_nodes`. Spatial filter is mutually exclusive with `ids` filter.

**Risk:** pg-schema-diff v1.0.2 may have issues with PostGIS extension tracking or functional GiST indexes. It already handles `CREATE EXTENSION "uuid-ossp"` and has `HAS_UNTRACKABLE_DEPENDENCIES` hazard flag. If functional indexes cause issues, we can create them via a separate post-migration step.

---

## 2. Make Node Labels, Names, and Links Optional

**Files to modify:**

- `database/42_nodes.sql` — change constraints

**Implementation:**

Change these 8 columns from `NOT NULL` to `NULL`:

- `name`
- `label_type`
- `label`
- `label_scale`
- `label_width`
- `label_height`
- `link_type`
- `link`

All label-related fields become nullable together (they only make sense as a group), same for link-related fields.

After modifying the SQL, regenerate DTOs. The generation logic in `scripts/src/scripts/generate_datamodels.py:94-118` already handles nullable → optional correctly, so no code changes beyond the schema.

---

## 3. Enhanced Localization Metrics

**Files to modify:**

- `packages/python/core/src/core/localization_metrics.py` — add fields to model
- `docker/localizer/src/build_metrics.py` — compute new metrics
- `docker/localizer/src/localize.py` — pass additional data to build_metrics
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs` — update rejection logic

**New metrics (all added to `LocalizationMetrics`):**

| Field                 | Type  | Purpose                                                    | Use                                                                                |
| --------------------- | ----- | ---------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `num_inliers`         | int   | Absolute RANSAC inlier count                               | **Rejection** — ratio alone is misleading (3/10 vs 300/1000 both 30%)              |
| `num_correspondences` | int   | Total 2D-3D matches fed to PnP                             | **Telemetry** — context for ratio, map quality indicator                           |
| `num_matches`         | int   | Raw LightGlue matches before 3D filtering                  | **Telemetry** — feature matching quality, compare mapping strategies               |
| `inlier_coverage`     | float | Convex hull area of inlier 2D positions / image area (0-1) | **Rejection** — inliers clustered in one corner = unreliable even if count is high |

Keep existing: `inlier_ratio`, `reprojection_error_median`.

**Computing `inlier_coverage`:** Use `scipy.spatial.ConvexHull` (already a dependency of `core`). In 2D, `ConvexHull.volume` gives area. Guard with `num_inliers >= 3` and try/except for degenerate cases (collinear points). Fall back to `0.0`.

**Computing `num_matches`:** Sum match counts across all image pairs from `match_indices` dict, computed right after LightGlue matching in `localize.py`.

**`build_localization_metrics` new signature:**

```python
def build_localization_metrics(
    pnp_result, points2d, points3d, pycolmap_camera,
    num_matches: int, image_width: int, image_height: int,
) -> LocalizationMetrics:
```

The `image_width`/`image_height` come from `transform_intrinsics(camera)` (already computed at `localize.py:110`).

**Data flow verification:** `LocalizationMetrics` (from `core`) is used directly in the localizer's `Localization` schema (`docker/localizer/src/schemas.py:24`), and the API router round-trips it via `model_validate(localization.metrics.model_dump())` (`docker/api/src/routers/localization.py:82`). New fields flow through automatically — no changes needed in API router or localizer schemas.

**Updated client rejection logic (`VisualPositioningSystem.cs:217`):**

Replace:

```csharp
if (localizationResult.Metrics.InlierRatio < .3f || localizationResult.Metrics.ReprojectionErrorMedian < 0.5f)
```

With:

```csharp
if (localizationResult.Metrics.NumInliers < MinInliers
    || localizationResult.Metrics.InlierRatio < MinInlierRatio
    || localizationResult.Metrics.InlierCoverage < MinInlierCoverage
    || localizationResult.Metrics.ReprojectionErrorMedian > MaxReprojectionErrorMedian)
```

Thresholds defined as named constants at the top of the class (easy to find and tune):

```csharp
private const float MinInliers = 20;
private const float MinInlierRatio = 0.3f;
private const float MinInlierCoverage = 0.05f;
private const float MaxReprojectionErrorMedian = 8.0f;
```

This replaces the indirect "low error = few inliers" heuristic with direct checks:

- `NumInliers < MinInliers` — minimum absolute count (the key new check)
- `InlierRatio < MinInlierRatio` — kept
- `InlierCoverage < MinInlierCoverage` — minimum spatial spread (5% of image)
- `ReprojectionErrorMedian > MaxReprojectionErrorMedian` — now correctly rejects HIGH error (not low)

---

## 4. Test Infrastructure (TDD)

No test suite exists. Add minimal pytest infrastructure targeting only the changed server-side surfaces.

**Setup — add to root `pyproject.toml`:**

```toml
[dependency-groups]
dev = [
    ...,
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
]
```

**Tests to write (before implementation):**

### a. `build_localization_metrics` unit tests

**File:** `docker/localizer/tests/test_build_metrics.py`

The new metrics (num_inliers, num_correspondences, num_matches, inlier_coverage) are pure numpy/scipy computations. Only the existing reprojection error uses pycolmap, which we mock.

Test cases:

- Correct `num_inliers` extraction from `pnp_result["num_inliers"]`
- Correct `num_correspondences` from `points2d.shape[0]`
- `num_matches` pass-through
- `inlier_coverage` for known point distributions (e.g., square of inliers covering 25% of image → 0.25)
- `inlier_coverage` edge cases: <3 inliers → 0.0, collinear inliers → 0.0
- `inlier_ratio` correctness (existing, verify not broken)

Mock `pycolmap.Camera.img_from_cam` to return identity-like projections for the reprojection error tests.

### b. Spatial query parameter validation tests

**File:** `docker/api/tests/test_spatial_queries.py`

Test the validation logic (doesn't need PostGIS):

- All four params provided → no validation error
- Partial params (e.g., position_x without radius) → raises `ClientException`
- Spatial params combined with `ids` → raises `ClientException` (mutually exclusive)
- No spatial params → no filter applied (passes through)

These test the route handler functions directly by calling them with a mock `AsyncSession`.

### c. Nullable node field tests

**File:** `docker/api/tests/test_nodes.py`

Test at the Pydantic DTO level (no database needed):

- `NodeCreate` with only position/rotation fields validates successfully
- `NodeCreate` with name=None, label=None, link=None validates successfully
- `NodeRead` correctly represents null fields

**Run tests:** `uv run pytest` from repo root.

---

## Execution Order

1. **Test infrastructure:** Add pytest dependencies to root `pyproject.toml`
2. **Write failing tests:** Create test files for build_metrics, spatial query validation, and nullable node DTOs
3. **PostGIS setup:** Update `.env.lock` (`POSTGRES_IMAGE` → `postgis/postgis:16-3.4-alpine`), add `postgis` extension to both `configure_database.template.sql` (creates it) and `database/00_extensions.sql` (desired state for pg-schema-diff)
4. **Schema changes:** Edit `database/42_nodes.sql` (make 8 columns nullable, add GiST index), add GiST index to `database/22_localization_maps.sql`
5. **Metrics model:** Edit `localization_metrics.py` (add 4 fields)
6. **Metrics computation:** Edit `build_metrics.py` (compute new metrics, new params)
7. **Localizer pipeline:** Edit `localize.py` (compute `num_matches`, pass data to build_metrics)
8. **API spatial queries:** Edit `localization_maps.py` and `nodes.py` (add `ST_3DDWithin` filtering)
9. **Run tests:** `uv run pytest` — verify all tests pass
10. **Regenerate:**
    - `uv run build` (rebuild with new postgres image)
    - `uv run up` (start services)
    - `uv run migrate-database` (apply schema + PostGIS extension + indexes)
    - `uv run generate-datamodels`
    - `uv run generate-clients --config openapi-projects.json`
11. **Client update:** Edit `VisualPositioningSystem.cs` (new rejection logic)
12. **Lint/typecheck:** `uv run ruff check .` / `uv run ruff format .` / `uv run basedpyright`

---

## Verification

- `uv run pytest` passes
- `uv run ruff check .` and `uv run basedpyright` pass
- Start services with `uv run up`
- **Spatial queries:** `GET /localization-maps?position_x=...&position_y=...&position_z=...&radius=...` returns only maps within radius. Same for `/nodes`. Omitting any one param returns validation error.
- **Optional node fields:** `POST /nodes` with only position/rotation fields succeeds (no name, label, or link required). `GET /nodes` returns null for omitted fields.
- **Metrics:** `POST /localize` response includes all 6 metric fields. Verify `num_inliers`, `num_correspondences`, `num_matches` are positive integers, `inlier_coverage` is between 0 and 1.
