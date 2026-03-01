---
id: T10
title: ZED capture Docker images + Renovate
status: ready
depends_on: []
---

# T10: ZED capture Docker images + Renovate

## Goal

Dockerfile and bake targets for `zed-capture-jp62`/`zed-capture-jp51`, Renovate config for auto-bumping Stereolabs base images, GitHub Actions build step.

## Context

Four-phase plan to modernize the ZED camera capture rig. This is Phase 1: self-healing CI/CD — auto-build new JetPack-specific Docker images whenever Stereolabs releases a new base image, using QEMU to spoof aarch64 during the build so `get_python_api.py` downloads the correct PyZED wheel automatically.

---

## 1a. One-time local environment setup

Confirm QEMU binfmt support and a multi-platform Buildx builder are available. These are prerequisites for all build tests in this phase.

```bash
docker run --privileged --rm tonistiigi/binfmt --install all
docker buildx create --name multiplatform --driver docker-container --use
docker buildx inspect --bootstrap
```

## 1b. `renovate.json`

**Harness — run before writing the file:**
```bash
docker run --rm \
  -v "$(pwd)/renovate.json":/usr/src/app/renovate.json \
  renovate/renovate renovate-config-validator /usr/src/app/renovate.json
```
Expect: failure (file doesn't exist). Red.

**Implementation — create `/renovate.json`:**

Create a Renovate configuration that watches the `stereolabs/zed` Docker Hub repository so that when Stereolabs drops a new JetPack base image, Renovate opens a PR updating the `ZED_BASE_IMAGE` ARG strings in the bake file.

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"],
  "docker": {
    "enabled": true
  },
  "packageRules": [
    {
      "matchDatasources": ["docker"],
      "matchPackageNames": ["stereolabs/zed"],
      "groupName": "ZED Base Image"
    }
  ]
}
```

**Verify:**
```bash
docker run --rm \
  -v "$(pwd)/renovate.json":/usr/src/app/renovate.json \
  renovate/renovate renovate-config-validator /usr/src/app/renovate.json
```
Expect: exit 0. Green.

## 1c. `compose.bake.yml` ZED targets + `docker/zed-capture/Dockerfile`

Add the bake targets before writing the Dockerfile so `--print` validates YAML resolution immediately, and the failing `--load` then drives writing the Dockerfile.

**Harness — validate bake YAML without pulling any images:**
```bash
docker buildx bake -f compose.bake.yml zed-capture-jp62 --print
```
Expect: failure (target doesn't exist). Red.

**Implementation — add ZED targets to `compose.bake.yml`:**

Add two new services following the existing `reconstructor-cuda` / `reconstructor-rocm` pattern:

```yaml
  zed-capture-jp62:
    build:
      context: .
      dockerfile: docker/zed-capture/Dockerfile
      args:
        <<: *base-args
        ZED_BASE_IMAGE: "stereolabs/zed:5.0-runtime-jetson-jp6.2"
      tags: [ "ghcr.io/outernet-foundation/placeframe/zed-capture:jp6.2" ]
      platforms: ["linux/arm64"]

  zed-capture-jp51:
    build:
      context: .
      dockerfile: docker/zed-capture/Dockerfile
      args:
        <<: *base-args
        ZED_BASE_IMAGE: "stereolabs/zed:4.2-runtime-jetson-jp5.1.2"
      tags: [ "ghcr.io/outernet-foundation/placeframe/zed-capture:jp5.1" ]
      platforms: ["linux/arm64"]
```

**Verify YAML resolution:**
```bash
docker buildx bake -f compose.bake.yml zed-capture-jp62 --print
```
Expect: resolved JSON printed, exit 0. Green for YAML. The Dockerfile is still missing, so proceed.

**Build harness — drive writing the Dockerfile:**
```bash
docker buildx bake -f compose.bake.yml zed-capture-jp62 --load
```
Expect: failure (Dockerfile missing). Red.

**Implementation — create `docker/zed-capture/Dockerfile`:**

Accepts `ZED_BASE_IMAGE` as a build ARG, installs `uv`, runs `get_python_api.py` (QEMU intercepts `platform.machine()` so it fetches the aarch64 wheel even on x86), copies the wheel into the vendored location, and installs the `zed` package via `uv sync`.

```dockerfile
ARG ZED_BASE_IMAGE=stereolabs/zed:5.0-runtime-jetson-jp6.2
FROM ${ZED_BASE_IMAGE}

ARG UV_BASE_DIGEST
FROM ${UV_BASE_DIGEST:-ghcr.io/astral-sh/uv:python3.13-bookworm-slim} AS uv

FROM ${ZED_BASE_IMAGE}

# Install uv
COPY --from=uv /uv /uvx /usr/local/bin/

# Download the correct PyZED wheel for this JetPack base.
# QEMU intercepts platform.machine() so get_python_api.py fetches the aarch64 wheel
# even when building on x86 GitHub Actions runners.
RUN python3 /usr/local/zed/get_python_api.py --target /tmp/pyzed_wheel
# Copy wheel into the vendored location so pyproject.toml path sources still resolve
RUN cp /tmp/pyzed_wheel/pyzed-*.whl zed/third-party/pyzed/

# Copy monorepo workspace files needed by the zed package
COPY pyproject.toml uv.lock ./
COPY packages/python/common ./packages/python/common
COPY packages/python/core ./packages/python/core
COPY zed ./zed

ENV UV_NO_CACHE=1
RUN uv sync --package zed --frozen --no-dev

CMD ["uv", "run", "--package", "zed", "--no-sync", \
     "uvicorn", "src.main:app", \
     "--app-dir", "zed", \
     "--host", "0.0.0.0", "--port", "9000"]
```

**Verify — build should now succeed:**
```bash
docker buildx bake -f compose.bake.yml zed-capture-jp62 --load
```
Expect: exit 0, image present in local daemon. Green.

## 1d. Renovate detection round-trip

With `renovate.json` and the `compose.bake.yml` ZED targets both written, verify Renovate detects the `stereolabs/zed` references and would open a PR on a version bump.

**B1 — dry-run against real Docker Hub:**
```bash
docker run --rm \
  -e LOG_LEVEL=debug \
  -v "$(pwd)":/usr/src/app \
  renovate/renovate \
    --platform=local \
    --dry-run=full \
    --config-file=/usr/src/app/renovate.json \
    .
```
Expect: output includes `"ZED Base Image"` group and references to the `stereolabs/zed` image. If the pinned tag is already the latest on Docker Hub, Renovate correctly reports "nothing to update" — this is not a failure; it means the config is wired correctly but there's nothing to bump right now. Proceed to B2 only in that case.

**B2 — local registry with fake newer tag (only needed if B1 reports "nothing to update"):**

```bash
# Start local registry
docker run -d -p 5000:5000 --name fake-registry registry:2

# Use alpine as a stand-in for the 7 GB ZED base
docker pull alpine:latest
docker tag alpine:latest localhost:5000/stereolabs/zed:5.0-runtime-jetson-jp6.2
docker push localhost:5000/stereolabs/zed:5.0-runtime-jetson-jp6.2

# The "new" version Renovate should detect
docker tag alpine:latest localhost:5000/stereolabs/zed:5.1-runtime-jetson-jp6.2
docker push localhost:5000/stereolabs/zed:5.1-runtime-jetson-jp6.2
```

Temporarily add `"registryUrls": ["http://localhost:5000"]` to the `packageRules` entry in `renovate.json`, and change both `ZED_BASE_IMAGE` values in `compose.bake.yml` to `localhost:5000/stereolabs/zed:5.0-runtime-jetson-jp6.2`. **Revert both before merging.**

```bash
docker run --rm \
  -e LOG_LEVEL=debug \
  --network=host \
  -v "$(pwd)":/usr/src/app \
  renovate/renovate \
    --platform=local \
    --dry-run=full \
    --config-file=/usr/src/app/renovate.json \
    .
```
Expect: Renovate reports a pending PR bumping `ZED_BASE_IMAGE` to `5.1-runtime-jetson-jp6.2`.

**Cleanup:**
```bash
docker stop fake-registry && docker rm fake-registry
# Revert renovate.json and compose.bake.yml patches
```

## 1e. `.github/workflows/build.yml`

**Harness — confirm `act` is installed and can parse the workflow:**
```bash
act push -W .github/workflows/build.yml --list
```
Expect: lists the `build-and-lock` job steps. If `act` isn't installed, that's the red state — install via `brew install act` / `winget install nektos.act`.

**Implementation — add ZED build step** after the existing ROCm build:

```yaml
      - name: Build ZED Capture Images
        run: |
          echo "::group::ZED Capture Images"
          docker buildx bake -f compose.bake.yml zed-capture-jp62 zed-capture-jp51 --push
          echo "::endgroup::"
```

This step does not need the free-disk-space workaround (no Torch layers).

**Verify:**
```bash
act push -W .github/workflows/build.yml \
  --secret GITHUB_TOKEN="$(gh auth token)" \
  -P ubuntu-latest=catthehacker/ubuntu:act-latest
```
Store secrets in a `.secrets` file (add to `.gitignore`) and pass with `--secret-file .secrets` if preferred. Expect: all steps including "Build ZED Capture Images" exit 0.

## Files to modify/create

| File | Action |
|---|---|
| `docker/zed-capture/Dockerfile` | Create new |
| `compose.bake.yml` | Add `zed-capture-jp62` / `zed-capture-jp51` targets |
| `.github/workflows/build.yml` | Add ZED capture build step |
| `renovate.json` | Create new |

## Verification

- `docker buildx bake -f compose.bake.yml zed-capture-jp62 --print` exits 0
- `renovate-config-validator renovate.json` exits 0
- Renovate dry-run output includes `"ZED Base Image"` group
- Push to `main` builds and pushes both tags to GHCR

## Done when

**Verifiable now (no special infra):**
- `docker buildx bake -f compose.bake.yml zed-capture-jp62 --print` exits 0
- Renovate config validates
- Workflow step added to `.github/workflows/build.yml`

**Requires QEMU (verify manually later):**
- Full image build succeeds
