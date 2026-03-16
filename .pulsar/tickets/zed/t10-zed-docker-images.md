---
id: T10
title: ZED capture Docker images
status: in-progress
plan: t10-plan.md
depends_on: []
---

# T10: ZED capture Docker images

## Goal

Dockerfile and bake target for `zed-capture`, dedicated CI build job in `build-unity.yml`, with QEMU cross-compilation for aarch64.

## Context

Four-phase plan to modernize the ZED camera capture rig. This is Phase 1: containerize the ZED capture service with Docker images built in CI and pushed to GHCR.

Currently the ZED service deploys via SSH/tarball (`zed/install.py`) to bare-metal Jetsons running systemd. This ticket containerizes it instead, with images built in CI and pushed to GHCR.

## Key files

| File | Action |
|---|---|
| `zed/Dockerfile` | Create — Dockerfile accepting `ZED_BASE_IMAGE` build ARG |
| `zed/entrypoint.sh` | Create — uvicorn startup script |
| `compose.bake.yml` | Modify — add `zed-capture` target |
| `build/src/build_scripts/placeframe/build_docker.py` | Modify — add `CROSS_COMPILE_TARGETS` to exclude ZED from default local builds |
| `.github/workflows/build-unity.yml` | Modify — add dedicated `build-zed` job with QEMU setup |
| `zed/pyproject.toml` | Modify — remove pyzed from dependencies and uv sources |
| `zed/third-party/pyzed/` | Delete — vendored wheels no longer needed |
| `typings/pyzed/` | Create — vendored type stubs so basedpyright resolves pyzed without the wheel |

## Approach

Dockerfile at `zed/Dockerfile` (not `docker/zed-capture/`) to work with `lock_python.py`'s workspace member discovery. No ARG defaults — bake targets pass `ZED_BASE_IMAGE` explicitly. pyzed is not a uv-managed dependency; it's installed at Docker build time via `get_python_api.py` from the ZED SDK in the base image. Vendored wheels are removed. Dedicated `build-zed` CI job (not a variant in the existing matrix) with QEMU for aarch64 cross-compilation. `CROSS_COMPILE_TARGETS` set in `build_docker.py` prevents auto-inclusion in local builds.

## Design decisions

- **No Dependabot.** Dropped from scope. ZED SDK releases are infrequent and version bumps need manual testing. Base image tags in `compose.bake.yml` are updated manually.
- **pyzed is not a uv dependency.** The real Stereolabs pyzed is not on PyPI (the PyPI `pyzed` is unrelated). It can only be obtained via `get_python_api.py` from a ZED SDK installation. It's installed in the Dockerfile at build time, outside uv's dependency graph.
- **Single target, ZED Box Mini only.** The original plan had two targets (jp62/jp51) for two JetPack generations. Simplified to one target (`zed-capture`) since only the ZED Box Mini (Orin-based, JetPack 6.x) is in use. Base image: `stereolabs/zed:5.2-runtime-jetson-jp6.1.0`.
- **Vendored pyzed type stubs.** Removing the pyzed wheel from dependencies meant basedpyright could no longer resolve `pyzed.sl` imports (214 errors in CI). Extracted `sl.pyi` from the SDK 5.0 wheel into `typings/pyzed/`, which basedpyright auto-discovers. Also required adding pyzed to deptry `DEP001` (missing dependency) ignore since it's imported but intentionally not declared.
- **Base image tag `5.2-runtime-jetson-jp6.1.0`.** The plan's original tag (`stereolabs/zed:5.0-runtime-jetson-jp6.2`) doesn't exist on Docker Hub. Stereolabs publishes SDK 5.2 images with `jp6.1.0` suffixes.
- **Dedicated CI job over variant.** The ZED build is materially different from the normal Docker builds (aarch64, QEMU, different base images). A standalone `build-zed` job is cleaner than cramming it into the existing `common`/`cuda`/`rocm` variant matrix.
- **Dockerfile at `zed/` not `docker/zed-capture/`.** `lock_python.py` discovers pylock-eligible packages by checking for `Dockerfile` in workspace member directories. `zed/` is already a member; creating `docker/zed-capture/` as a new member would require restructuring.

## Done when

**Verifiable now (no special infra):**
- `docker buildx bake -f compose.bake.yml zed-capture --print` exits 0
- `build-zed` job present in `build-unity.yml` with QEMU setup
- pyzed removed from `zed/pyproject.toml` dependencies
- `zed/third-party/pyzed/` deleted
- CI preflight passes (basedpyright, deptry, ruff)

**Requires QEMU (verify manually later):**
- Full image build succeeds on aarch64 via QEMU cross-compilation

## Next step

Waiting for CI `build-zed` job to pass with the corrected base image tag.
