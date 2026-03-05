---
id: T70
title: Automate Cesium native Linux build and publish to UPM registry
status: plan-needed
depends_on: [T69, T71]
---

# T70: Automate Cesium native Linux build and publish to UPM registry

## Goal

Move the manual Cesium native Linux build (T69) into CI and publish the resulting package to the scoped UPM registry. Remove the committed binary from the repo.

## Context

T69 commits a manually-built forked `com.cesium.unity` package with Linux binaries directly to the repo as a temporary measure. This ticket replaces that with an automated build that publishes to the same scoped registry set up in T71 (npmjs.org with OIDC trusted publishing).

The build script already exists at `scripts/build-cesium-native-linux.sh` — it's idempotent and handles the full process: clone cesium-unity-samples, clone cesium-unity into its Packages/, publish Reinterop, open in Unity on Linux (triggers code generation), cmake build, strip binaries. As part of this ticket, convert it to a Python script in `scripts/src/scripts/` (consistent with the rest of the repo's tooling, uses `common.run_command`, gets basedpyright checking). Register as `uv run build-cesium-native-linux`. The CI workflow calls the Python script.

## Key files

- `scripts/build-cesium-native-linux.sh` — existing shell script from T69 (to be converted to Python)
- `scripts/src/scripts/build_cesium_native_linux.py` — new Python script (replaces shell script)
- `packages/unity/com.cesium.unity/` — forked package with committed Linux binaries (to be removed)
- `.github/workflows/publish-upm.yml` — existing publish workflow (may extend or create separate)
- `apps/MapRegistrationTool/Packages/manifest.json` — consumer manifest (switch from `file:` to registry)
- `legacy/Outernet.Client/Packages/manifest.json` — consumer manifest (switch from `file:` to registry)

## Done when

- [ ] Build script converted from shell to Python (`uv run build-cesium-native-linux`)
- [ ] CI workflow builds CesiumForUnityNative for Linux from source
- [ ] Built package published to npmjs.org under `org.outernet` scope via OIDC trusted publishing
- [ ] Consumer manifests point at registry instead of `file:` path
- [ ] Committed binary (`packages/unity/com.cesium.unity/`) removed from repo
- [ ] Rebuild triggers documented (manual or on Cesium version bump)
