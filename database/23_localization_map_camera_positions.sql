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
