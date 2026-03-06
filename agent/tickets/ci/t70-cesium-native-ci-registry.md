---
id: T70
title: Automate Cesium native Linux build, repackage with official binaries, publish to UPM registry
status: in-progress
depends_on: [T69, T71]
plan: t70-plan.md # Steps 1-6 still accurate; step 8 (Prepare package) is superseded — now downloads official .tgz and merges non-Linux binaries instead of copying Linux-only .so files
---

# T70: Automate Cesium native Linux build, repackage with official binaries, publish to UPM registry

## Goal

Build the Cesium for Unity native plugin for Linux (the one platform upstream doesn't support) in CI, merge those binaries with the official release's pre-built binaries for all other platforms (Windows, macOS, Android, iOS), and publish the combined multi-platform package to the scoped UPM registry. Remove the committed binary from the repo.

## Context

T69 commits a manually-built forked `com.cesium.unity` package with Linux-only binaries directly to the repo as a temporary measure. This ticket replaces that with an automated build that publishes to the same scoped registry set up in T71 (npmjs.org with OIDC trusted publishing).

The upstream Cesium for Unity package (`com.cesium.unity`) ships native binaries for Windows, macOS, Android, and iOS — but not Linux. Our fork exists solely to add Linux support. Rather than building for every platform ourselves, we build only Linux and repackage the official release's pre-built binaries for all other platforms into a single combined package. This gives consumers a drop-in replacement that works on all platforms.

The build script already exists at `scripts/build-cesium-native-linux.sh` — it's idempotent and handles the full process: clone cesium-unity-samples, clone cesium-unity into its Packages/, publish Reinterop, open in Unity on Linux (triggers code generation), cmake build, strip binaries. As part of this ticket, convert it to a Python script in `scripts/src/scripts/` (consistent with the rest of the repo's tooling, uses `common.run_command`, gets basedpyright checking). Register as `uv run build-cesium-native-linux`. The CI workflow calls the Python script.

## Key files

- `scripts/build-cesium-native-linux.sh` — existing shell script from T69 (to be converted to Python)
- `scripts/src/scripts/build_cesium_native_linux.py` — new Python script (replaces shell script)
- `packages/unity/com.cesium.unity/` — forked package with committed Linux binaries (to be removed)
- `.github/workflows/build-cesium-native.yml` — CI workflow (already created, needs repackaging step)
- `apps/MapRegistrationTool/Packages/manifest.json` — consumer manifest (switch from `file:` to registry)
- `legacy/Outernet.Client/Packages/manifest.json` — consumer manifest (switch from `file:` to registry)

## Done when

- [ ] Build script converted from shell to Python (`uv run build-cesium-native-linux`)
- [ ] CI workflow builds CesiumForUnityNative for Linux from source
- [ ] CI workflow downloads official Cesium release and extracts non-Linux native binaries (Windows, macOS, Android, iOS)
- [ ] Linux-built binaries merged with official binaries into a single multi-platform package
- [ ] Combined package published to npmjs.org under `org.outernet` scope via OIDC trusted publishing
- [ ] Consumer manifests point at registry instead of `file:` path
- [ ] Committed binary (`packages/unity/com.cesium.unity/`) removed from repo
- [ ] Rebuild triggers documented (manual or on Cesium version bump)

## Approach

Build only Linux native binaries (the one platform upstream doesn't support), then download the official Cesium for Unity release `.tgz` for the same version and extract its pre-built binaries for Windows, macOS, Android, and iOS. Merge both into a single `org.outernet.cesium-unity` package and publish to npmjs.org. This avoids cross-compiling for every platform — we only build what upstream doesn't provide.

CI workflow (`build-cesium-native.yml`) uses `unityci/editor` container with serial license activation, caches vcpkg/cmake artifacts via ORAS/GHCR, and publishes with OIDC trusted publishing. Consumer manifests switch from `file:` to registry. Version drops the `-linux` qualifier since the package is now multi-platform.

## Design decisions

- Package renamed from `com.cesium.unity` to `org.outernet.cesium-unity` to fit the `org.outernet` scoped registry
- Separate workflow from `publish-upm.yml` — fundamentally different job (30-60 min cmake build vs quick npm publish)
- `workflow_dispatch` only (manual trigger) — Cesium version bumps are rare
- vcpkg/cmake caching via ORAS/GHCR to avoid 30-60 min rebuilds
- `GIT_LFS_SKIP_SMUDGE=1` required in CI — `unityci/editor` has git-lfs installed, which breaks vcpkg's KTX port (LFS smudge filter fails in temp clone). COI sandbox lacks git-lfs so it works locally.
- Apache-2.0 redistribution: fork is compliant as long as LICENSE is included in published package and package name doesn't imply official Cesium endorsement
- Codegen output cache replaces Unity Library cache — the Library cache caused Reinterop to never fire on warm runs (Unity skipped recompilation, so code generation never ran). Caching just the outputs (Reinterop.dll + generated C++ headers) lets phase_codegen skip Unity entirely via idempotency checks, which is both faster and correct.
- Repackage official binaries instead of building for every platform — upstream doesn't support Linux but ships pre-built binaries for Windows, macOS, Android, and iOS. We build Linux and borrow the rest from the official release `.tgz`. This keeps CI to a single Linux runner and avoids cross-compilation complexity.
- Windows excluded from consumer manifests for now — T75 blocks win64 IL2CPP builds (no Windows runner yet), so the Windows binaries are included in the package but not yet exercised in CI builds.

## Next step

CI is green — multi-platform package published to npmjs.org as `org.outernet.cesium-unity@1.15.3-1` via OIDC trusted publishing. Repackaging merges official Windows + Android binaries with Linux-built `.so` files (macOS/iOS/WSA excluded to stay under npm's 200 MB limit).

Completed:

1. ~~Add repackaging step to workflow~~ done
2. ~~Bump version and drop `-linux` qualifier~~ done (→ `1.15.3-1`)
3. ~~Configure OIDC trusted publishing on npmjs.org~~ done
4. ~~Test OIDC publish~~ done (CI run passed, package published)
5. ~~Update consumer manifests~~ done (MapRegistrationTool + Outernet.Client → `1.15.3-1`)
6. ~~Remove committed binaries~~ done (deleted `.so` files, added to `.gitignore`)
7. ~~Regenerate packages-lock.json~~ done (both projects, pre-existing compilation errors from stale `org.nuget.placeframeapiclient` — tracked in T86)

Remaining:

1. **Remove push trigger**: delete the push trigger from `build-cesium-native.yml` (used for testing, should be `workflow_dispatch` only before merging to main).
2. **Unity compilation errors**: both consumer projects have pre-existing `error CS` from stale `org.nuget.placeframeapiclient@0.1.3` on npm (missing `NumInliers`, `InlierCoverage`, etc.). Tracked in T86.
