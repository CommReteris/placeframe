# Plan: Migrate database-migrator to Python + add --temp-db-dsn support

## Context

The `migrate-database` Docker container currently uses a bash entrypoint that calls `pg-schema-diff apply` as `placeframe_owner`. This fails when the DDL includes `CREATE EXTENSION postgis` because PostGIS is an untrusted extension requiring superuser privileges — even in pg-schema-diff's temporary "desired state" database.

**Fix**: Use pg-schema-diff's `--temp-db-dsn` flag to provide superuser credentials for the temp DB while keeping the owner credentials for the actual migration apply. Additionally, convert the bash-only container to a Python package following the existing Docker service pattern.

## Changes

### 1. Create `docker/database-migrator/` Python package

New files:

- **`docker/database-migrator/pyproject.toml`** — minimal deps: `common`, `typer>=0.17.4`
  - Console script: `database-migrator = "database_migrator.main:main"`
  - Follow database-manager pattern (hatchling build, `src/database_migrator/` wheel package)

- **`docker/database-migrator/src/database_migrator/__init__.py`** — empty

- **`docker/database-migrator/src/database_migrator/main.py`** — core logic:
  - Use `common.run_command.exec_command()` to exec pg-schema-diff (replaces current process, like other services)
  - Read config from env vars: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_ADMIN_USER`, `DB_ADMIN_PASSWORD`, `DATABASE_SCHEMA_DIR`, `ALLOWED_HAZARDS`, `EXTRA_PGOPTIONS`
  - Build two DSNs: owner (`--from-dsn`) and admin (`--temp-db-dsn`)
  - Construct and exec the `pg-schema-diff apply` command
  - Reuse `_find_pg_schema_diff()` helper from current `scripts/migrate_database.py`

### 2. Update Dockerfile: `docker/database-migrator/Dockerfile`

Multi-stage build:
- **Stage 1** (Go, from current Dockerfile): compile `pg-schema-diff` binary
- **Stage 2** (uv base image, matching database-manager pattern):
  - Set standard Python env vars (`PYTHONUNBUFFERED`, `UV_COMPILE_BYTECODE`, etc.)
  - `uv venv`, install from `pylock.toml`, install `common` + `database-migrator` with `--no-deps`
  - `COPY --from=build /go/bin/pg-schema-diff /usr/local/bin/pg-schema-diff`
  - Copy entrypoint, set `ENTRYPOINT`

### 3. Update entrypoint: `docker/database-migrator/entrypoint.sh`

Minimal bash shim (matching database-manager pattern):
```bash
exec uv run --no-sync database-migrator
```

### 4. Update `compose.yml`

Add admin credentials to `migrate-database` service environment:
```yaml
DB_ADMIN_USER: "${POSTGRES_ADMIN_USER:?err}"
DB_ADMIN_PASSWORD: "${POSTGRES_ADMIN_PASSWORD:?err}"
```

### 5. Add to workspace: `pyproject.toml` (root)

Add `"docker/database-migrator"` to `[tool.uv.workspace] members`.

### 6. Update `scripts/src/scripts/migrate_database.py`

Update the local dev script to also pass `--temp-db-dsn` with admin credentials (localhost defaults: `postgres:password@localhost:55432/placeframe`).

### 7. Generate `docker/database-migrator/pylock.toml`

Run `uv run generate-lock-files` (or manually generate) to create the lock file for the new package.

## Files to modify

| File | Action |
|------|--------|
| `docker/database-migrator/pyproject.toml` | Create |
| `docker/database-migrator/src/database_migrator/__init__.py` | Create |
| `docker/database-migrator/src/database_migrator/main.py` | Create |
| `docker/database-migrator/Dockerfile` | Rewrite |
| `docker/database-migrator/entrypoint.sh` | Rewrite |
| `compose.yml` | Edit (add admin env vars) |
| `pyproject.toml` (root) | Edit (add workspace member) |
| `scripts/src/scripts/migrate_database.py` | Edit (add --temp-db-dsn) |

## Key references

- Database-manager pattern: `docker/database-manager/Dockerfile`, `docker/database-manager/pyproject.toml`, `docker/database-manager/entrypoint.sh`
- `common.run_command.exec_command()`: `packages/python/common/src/common/run_command.py` — replaces current process via `os.execvpe`
- Existing migrate script: `scripts/src/scripts/migrate_database.py`
- Go build for pg-schema-diff: current `docker/database-migrator/Dockerfile` stage 1

## Verification

1. Run `uv run generate-lock-files` to generate `pylock.toml` for the new package
2. Run `uv run build` to build the updated Docker image
3. Run `uv run up --gpu none` and verify the migrate-database container starts and completes successfully
4. Check `docker logs placeframe-migrate-database-1` for clean migration output
5. Verify `uv run ruff check .` and `uv run basedpyright` pass
