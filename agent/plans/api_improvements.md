# Plan: Fix Nullable Columns + Refactor Localization Map Radius Search

## Context

Commit `43413fa2` ("Add PostGIS spatial queries and make node metadata nullable") introduced two issues:
1. **Bug**: `link_type` and `label_type` columns in `nodes` were made nullable but should remain NOT NULL (no defaults — clients must provide them)
2. **Feature gap**: The radius search on `GET /localization-maps` only checks distance to the map's single registration point, but should check against all reconstructed camera positions — matching if ANY camera position is within the search radius

This is for large outdoor environments. Verticality is handled by separate maps per floor, not within a single map. A convex hull is NOT the right semantic — an arc-shaped map would incorrectly match query points in the "elbow." Individual camera positions are the correct representation of actual map coverage.

---

## Part 1: Fix `link_type` and `label_type` to NOT NULL

**File**: `database/42_nodes.sql`

- Line 45-46: `label_type label_type NULL` → `label_type label_type NOT NULL`
- Line 49-50: `link_type link_type NULL` → `link_type link_type NOT NULL`

No DEFAULT values. Clients must always provide both fields. No backfill needed (dev system).

**Downstream**: Regenerate datamodels — `NodeCreate`/`NodeRead` DTOs will make these fields required.

---

## Part 2: New Table for Camera Positions

**New file**: `database/23_localization_map_camera_positions.sql`

```sql
CREATE TABLE localization_map_camera_positions (
    tenant_id uuid
        NOT NULL
        REFERENCES auth.tenants(id)
        ON DELETE RESTRICT
        DEFAULT current_tenant(),
    localization_map_id uuid
        NOT NULL
        REFERENCES localization_maps(id)
        ON DELETE CASCADE,
    position_x double precision NOT NULL,
    position_y double precision NOT NULL,
    position_z double precision NOT NULL,
    id uuid NOT NULL PRIMARY KEY DEFAULT gen_random_uuid()
);

ALTER TABLE localization_map_camera_positions ENABLE ROW LEVEL SECURITY;

CREATE POLICY localization_map_camera_positions_rls_policy
  ON localization_map_camera_positions
  FOR ALL
    USING (tenant_id = current_tenant())
    WITH CHECK (tenant_id = current_tenant());

CREATE INDEX idx_lm_camera_positions_gist
  ON localization_map_camera_positions
  USING GIST (ST_MakePoint(position_x, position_y, position_z));

CREATE INDEX idx_lm_camera_positions_map_id
  ON localization_map_camera_positions (localization_map_id);
```

Includes `tenant_id` + RLS to match project convention. Separate table with individual point rows for optimal GIST index performance (each point indexed individually, not a bounding box over a MultiPoint).

---

## Part 3: Populate Camera Positions on Map Create/Update

**New helper module**: `docker/api/src/routers/camera_positions.py`

### `compute_world_camera_positions(reconstruction_id, position, rotation)`
1. Fetch `{reconstruction_id}/sfm_model/frame_poses.npz` from S3 (reuse S3 client pattern from `docker/api/src/routers/reconstructions.py`)
2. Load `positions` array (N, 3) — camera positions in reconstruction coordinate frame
3. Apply registration transform: `world_pos = R @ recon_pos + T`
   - R = rotation matrix from quaternion (rotation_x/y/z/w) via `scipy.spatial.transform.Rotation`
   - T = translation vector (position_x/y/z)
4. Return list of (x, y, z) tuples in world coordinates

### `replace_camera_positions(session, localization_map_id, tenant_id, world_positions)`
1. DELETE existing rows for this map_id (only relevant for PATCH — on CREATE there are none)
2. Bulk INSERT new rows (with tenant_id)

Note: DELETE-then-INSERT is the update strategy for PATCH when the registration transform changes. On CREATE, the DELETE is a no-op. This is not an error condition — it's expected that positions exist when re-registering a map.

### Integration in `docker/api/src/routers/localization_maps.py`:
- **`create_localization_map`**: After flush/refresh, compute and store positions
- **`update_localization_map`**: If any registration field changed (position_x/y/z, rotation_x/y/z/w), recompute
- **`update_localization_maps`** (batch): Same, per map

**Error handling**: If frame_poses.npz doesn't exist in S3, log warning and store zero positions.

**DB vs NPZ endpoints**: The existing `GET /reconstructions/{id}/frame_poses` endpoint returns positions in reconstruction-local coordinates (from the NPZ) for use by the localizer. The new DB rows store world/ECEF positions for spatial queries. Different coordinate frames, different consumers — both stay.

---

## Part 4: Modify Spatial Queries + Delete Helper

**Delete**: `docker/api/src/routers/spatial.py` — remove entirely. The node and localization map spatial filters are now different, so a shared helper adds no value. Inline each filter directly in its router.

**File**: `docker/api/src/routers/nodes.py`

Inline the spatial parameter validation and `ST_3DDWithin` filter directly. Move the `validate_spatial_params` logic and `apply_spatial_filter` call inline into `get_nodes`. Remove the import of `spatial.py`.

**File**: `docker/api/src/routers/localization_maps.py`

Inline spatial parameter validation. Replace the point-based filter with an EXISTS subquery against camera positions:

```python
# In fetch_localization_maps, when spatial params are provided:
query = query.where(
    exists(
        select(1)
        .where(LocalizationMapCameraPosition.localization_map_id == LocalizationMap.id)
        .where(func.ST_3DDWithin(
            func.ST_MakePoint(
                LocalizationMapCameraPosition.position_x,
                LocalizationMapCameraPosition.position_y,
                LocalizationMapCameraPosition.position_z),
            func.ST_MakePoint(position_x, position_y, position_z),
            radius))
    )
)
```

EXISTS is optimal here: the GIST index handles the spatial predicate, the B-tree index on `localization_map_id` handles correlation, and EXISTS short-circuits after the first matching camera position (doesn't scan all N cameras per map).

---

## Part 5: Regeneration Pipeline

After schema changes:
1. `uv run up --gpu none` — applies migrations (timeout: 600000)
2. `uv run generate-datamodels` — regenerates SQLAlchemy models + Pydantic DTOs
3. `uv run generate-lock-files`
4. `uv run generate-clients --config openapi-projects.json --project docker/api`

No backfill needed (dev system, no existing data).

---

## Files to Modify/Create

| File | Action |
|---|---|
| `database/42_nodes.sql` | Change label_type, link_type to NOT NULL |
| `database/23_localization_map_camera_positions.sql` | **New**: camera positions table with RLS + indexes |
| `docker/api/src/routers/camera_positions.py` | **New**: S3 fetch, coordinate transform, DB persistence |
| `docker/api/src/routers/spatial.py` | **Delete**: no longer needed |
| `docker/api/src/routers/nodes.py` | Inline spatial filter (was imported from spatial.py) |
| `docker/api/src/routers/localization_maps.py` | Integrate camera position compute on create/update, inline EXISTS spatial filter |
| `packages/generated/` | Regenerate (datamodels, api-client, csharp api-client) |

---

## Verification

1. `uv run ruff check .` and `uv run basedpyright` pass
2. `uv run pytest` — existing tests pass
3. Manual: Create a localization map via API → verify camera position rows appear in DB
4. Manual: Query `GET /localization-maps?position_x=...&radius=...` → verify maps found by camera positions, not just registration point
5. Manual: PATCH a map's registration transform → verify camera positions recomputed
6. Manual: DELETE a map → verify camera positions cascade-deleted
