---
id: T2
title: Replace .env.lock built-image digests with SHA-based image tags
status: plan-needed
depends_on: []
---

# T2: Replace .env.lock built-image digests with SHA-based image tags

## Goal

Eliminate `.env.lock` as the mechanism for pinning built (repo-owned) Docker images. Instead, tag images with the git commit SHA and reference them by SHA in `compose.yml`. This removes the second source of main-only commits (the `.env.lock` merge in `commit_artifacts.py`) and means anyone can `uv run up` on any commit to get exactly the images CI built for that commit.

## Context

Currently `.env.lock` contains two categories of values:

**Base/third-party image digests** (correct to pin):
```
ALPINE_DIGEST=@sha256:a4f4213a...
POSTGRES_IMAGE=docker.io/postgis/postgis:16-3.4-alpine@sha256:9b98836d...
KEYCLOAK_IMAGE=quay.io/keycloak/keycloak:26.3.5@sha256:...
```
These images come from external registries where tags can float. Digest pinning is the only way to guarantee reproducibility.

**Built image digests** (wrong to pin this way):
```
API_IMAGE=ghcr.io/outernet-foundation/placeframe/api:latest@sha256:1ac66edd...
LOCALIZER_CUDA_IMAGE=ghcr.io/outernet-foundation/placeframe/localizer-cuda:latest@sha256:...
```
These images are built from repo code. The image is a deterministic function of the code commit + base image digest + Dockerfile. If you know the commit SHA and the base images are pinned, you know exactly what the image contains. The digest in `.env.lock` adds no information — it's just a cache key.

### Current flow

1. CI `build-docker` job (3 variants: common, cuda, rocm) builds images via `docker buildx bake`, pushes to GHCR with `:latest` tag, uploads per-variant `.env.lock` as artifact
2. CI `commit` job downloads all variant `.env.lock` artifacts, merges them (`commit_artifacts.py` `_merge_env_locks()`), commits the merged `.env.lock` to the current branch
3. `uv run up` reads `.env.lock` (or `.env.local.lock` for local builds), passes as `--env-file` to `docker compose`, which substitutes `${API_IMAGE:?err}` etc.

### Proposed flow

1. CI `build-docker` builds images, pushes to GHCR with `:<commit-sha>` tag (and optionally `:latest`)
2. No commit step needed for built images — the SHA is implicit
3. `uv run up` computes `GIT_SHA=$(git rev-parse HEAD)`, passes to `docker compose` as env var
4. `compose.yml` references built images as `ghcr.io/.../api:${GIT_SHA}`
5. For local builds: `uv run build` writes local image IDs to `.env.local.lock` (gitignored), `uv run up` prefers it when present — identical to current behavior

### What happens to `.env.lock`

`.env.lock` is reduced to **base/third-party digests only**. It becomes a developer-committed file, updated intentionally via `uv run build --upgrade` (which re-resolves base image digests). CI does not modify it.

The merge logic in `commit_artifacts.py` that combines per-variant lock files becomes unnecessary for base images (base image digests are the same across all variants — they're resolved via `docker buildx imagetools inspect`, not built). The per-variant `.env.lock` upload/download/merge flow can be simplified or removed.

### `.env.local.lock` behavior

Unchanged. Local builds (`uv run build` / `uv run build --mode local`) write local image IDs to `.env.local.lock`. `uv run up` checks for `.env.local.lock` first and uses it as an override. This file stays gitignored.

The key difference: `.env.local.lock` currently contains both base/third-party digests AND built image IDs. After this change, it only needs built image IDs (base/third-party come from the committed `.env.lock`). But for simplicity, it can continue to contain both — `up.py` just needs to layer them correctly (`.env.local.lock` overrides `.env.lock` for any overlapping keys).

### Compose variable substitution

Currently every service has:
```yaml
api:
  x-image-ref: "ghcr.io/outernet-foundation/placeframe/api:latest"
  image: "${API_IMAGE:?err}"
```

After this change, built services become:
```yaml
api:
  image: "ghcr.io/outernet-foundation/placeframe/api:${GIT_SHA:?err}"
```

Third-party services keep their current pattern:
```yaml
postgres:
  x-image-ref: "docker.io/postgis/postgis:16-3.4-alpine"
  image: "${POSTGRES_IMAGE:?err}"
```

The `x-image-ref` field on built services becomes unnecessary (the image name is hardcoded, the tag is the SHA). It could be removed or kept for documentation.

### GPU variant image naming

GPU-specific services have separate images: `localizer-cuda`, `localizer-rocm`, `reconstructor-cuda`, `reconstructor-rocm`. These are defined in `compose.bake.yml` with separate targets. Each gets its own GHCR image name. The SHA tag applies to all of them — same commit, same tag, different image names.

In `compose.cuda.yml` / `compose.rocm.yml` (GPU override files), the image references would change from `${LOCALIZER_CUDA_IMAGE:?err}` to `ghcr.io/.../localizer-cuda:${GIT_SHA:?err}`.

## Key files

**Modify:**
- `build/src/build_scripts/placeframe/build_docker.py` — tag built images with commit SHA instead of (or in addition to) `:latest`; in CI mode, push with SHA tag; stop writing built-image entries to `.env.lock`; `.env.lock` writes become base/third-party only
- `build/src/build_scripts/placeframe/up.py` — compute `GIT_SHA` from `git rev-parse HEAD`, pass as env var to docker compose; layer `.env.local.lock` over `.env.lock` for local override
- `compose.yml` — change built-service `image:` fields from `${SERVICE_IMAGE:?err}` to `ghcr.io/.../service:${GIT_SHA:?err}`; keep third-party services as `${SERVICE_IMAGE:?err}`
- `compose.bake.yml` — update build target tags to include SHA (may need to accept SHA as variable)
- `compose.cuda.yml` / `compose.rocm.yml` — update GPU-specific image references
- `build/src/build_scripts/placeframe/ci/commit_artifacts.py` — remove `.env.lock` merge logic and commit; this script may become unnecessary (delete if T1 also removes its other responsibilities)
- `.github/workflows/placeframe.yml` — remove `.env.lock` from `paths-ignore`; remove env-lock artifact upload from `build-docker` job; remove env-lock artifact download and merge from `commit` job

**Reduce:**
- `.env.lock` — remove all `*_IMAGE` entries for built services; keep only `*_DIGEST` (base images) and `*_IMAGE` entries for third-party pulled services (postgres, keycloak, minio, etc.)

## Approach

1. Update `compose.yml` and GPU override files: change built-service image refs to `ghcr.io/.../service:${GIT_SHA:?err}`, keep third-party refs as-is
2. Update `compose.bake.yml`: add SHA-based tagging to build targets (accept `GIT_SHA` as a variable for the tag)
3. Update `build_docker.py`: compute SHA, pass as tag to buildx bake, stop writing built-image digests to lock files; base/third-party resolution unchanged
4. Update `up.py`: compute `GIT_SHA`, pass to docker compose; keep `.env.local.lock` override logic
5. Strip built-image entries from `.env.lock`, keep base/third-party only
6. Update workflow: remove env-lock artifact upload/download/merge steps
7. Update or delete `commit_artifacts.py` depending on T1 status

## Done when

**Verifiable now:**
- [ ] `compose.yml` built-service images reference `ghcr.io/.../:${GIT_SHA:?err}`
- [ ] `compose.yml` third-party services still reference `${SERVICE_IMAGE:?err}` from `.env.lock`
- [ ] `compose.bake.yml` build targets tag with commit SHA
- [ ] `build_docker.py` pushes SHA-tagged images in CI mode
- [ ] `build_docker.py` does not write built-image digests to `.env.lock`
- [ ] `.env.lock` contains only base image digests and third-party image references
- [ ] `up.py` computes and passes `GIT_SHA` to docker compose
- [ ] `up.py` still uses `.env.local.lock` as override for local builds
- [ ] Workflow no longer uploads/downloads/merges env-lock artifacts for built images
- [ ] `commit_artifacts.py` no longer commits `.env.lock` (or is deleted)

**Requires manual verification:**
- [ ] `uv run up` on a commit where CI has run pulls the correct SHA-tagged images from GHCR
- [ ] `uv run up` after local `uv run build` uses locally-built images
- [ ] Checking out an old commit and running `uv run up` pulls historical images
- [ ] `uv run up` fails with a clear error if images haven't been built for the current SHA
- [ ] `uv run build --upgrade` still updates base/third-party digests in `.env.lock`

## Next step

Enter plan mode to detail: how `GIT_SHA` flows through compose variable substitution (does compose support env vars not in an env-file?), how `compose.bake.yml` accepts the SHA for tagging, and whether `.env.local.lock` needs format changes or just continues working via key override.
