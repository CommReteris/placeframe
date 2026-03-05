---
id: T86
title: Pre-built Docker image for Cesium native Linux build
status: plan-needed
depends_on: [T70]
---

# T86: Pre-built Docker image for Cesium native Linux build

## Goal

Eliminate the ~5 minute `apt-get update && apt-get install` step from the Cesium native build CI workflow by baking build dependencies into a custom Docker image.

## Context

The `build-cesium-native.yml` workflow runs inside `unityci/editor:6000.0.66f1-linux-il2cpp-3` and installs `cmake`, `ninja-build`, `nasm`, `g++`, `zip`, `unzip`, `curl`, `pkg-config`, and `zstd` on every run. This adds ~5 minutes to a build that already takes 30-60 minutes cold. Since the dependency list is stable (only changes on Unity or toolchain version bumps), these can be baked into a derived image.

## Key files

- `.github/workflows/build-cesium-native.yml` — update container image reference, remove `Install build dependencies` step
- `docker/cesium-builder/Dockerfile` (new) — `FROM unityci/editor:6000.0.66f1-linux-il2cpp-3` with build deps pre-installed
- `.github/workflows/build-cesium-builder-image.yml` (new) — build and push the image to GHCR on changes to the Dockerfile

## Approach

Create a Dockerfile that extends `unityci/editor` with the build dependencies pre-installed. Build and push to GHCR via a small workflow triggered on Dockerfile changes. Update `build-cesium-native.yml` to reference the GHCR image instead of `unityci/editor` directly.

## Done when

- [ ] Dockerfile exists with build deps baked in
- [ ] Image is published to GHCR
- [ ] `build-cesium-native.yml` uses the new image and has no `Install build dependencies` step
- [ ] Cesium native build still completes successfully
