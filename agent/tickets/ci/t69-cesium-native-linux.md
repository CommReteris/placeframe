---
id: T69
title: Build Cesium for Unity native plugin for Linux
status: in-progress
depends_on: []
plan: t69-plan.md
---

# T69: Build Cesium for Unity native plugin for Linux

## Goal

Get Outernet.Client's Cesium dependency compiling and entering Play Mode on Linux, so `uv run build-unity` passes for that project.

## Context

`com.cesium.unity` v1.15.4 ships native binaries for Windows, macOS, Android, iOS, and UWP — but not Linux. The generated C# interop layer is wrapped in `#if UNITY_EDITOR_WIN` / `#if UNITY_EDITOR_OSX` guards with no `#if UNITY_EDITOR_LINUX` block, so the entire Reinterop layer compiles out on Linux, producing CS0246 errors for `ReinteropNativeImplementation`.

There is no official Linux support and no indication it's on the roadmap (GitHub issue [#513](https://github.com/CesiumGS/cesium-unity/issues/513)). A community guide exists for v1.15.3: [JOHNI1/CesiumSetupLinuxGuide](https://github.com/JOHNI1/CesiumSetupLinuxGuide).

Research report: `agent/research/cesium-unity-native-linux.md`

## Design decisions

1. **Artifact hosting**: Build manually once, commit the forked package to the repo as a local file path dependency (`"file:../../packages/cesium-unity-linux"`). Follow-up ticket to move the build to CI and publish to a scoped registry (same one being set up for Placeframe UPM packages).
2. **Augment vs. replace**: Fork of the official `com.cesium.unity` package — same name, superset contents. Adds Linux `.so` binaries and `#if UNITY_EDITOR_LINUX` generated C# alongside the existing Win/Mac/Android/iOS binaries. Outernet.Client's manifest points at the local fork instead of Cesium's registry.
3. **Build location**: Built manually once outside the repo. The resulting package (including `.so`) is committed to the repo temporarily. Follow-up ticket moves the build to CI and the artifact to a registry.
4. **Play Mode bar**: "Loads without crashing" is sufficient. No need for specific Cesium geospatial functionality to work.
5. **Version tracking**: Manual for now. Follow-up ticket to automate via CI.
6. **Fork scope**: C# code + Linux `.so` files only (~100-150MB). No other platform binaries (saves ~1.3GB). All original C# platform guards preserved so compilation works everywhere; other platforms lose runtime/Play Mode from this fork but can switch back to the official registry.
7. **Build automation**: Native `.so` files built via an idempotent shell script committed to the repo. Script installs deps, clones source, and builds regardless of container starting state — serves as both build tool and documentation.
8. **C# guard generation**: Reinterop source generator handles Linux C# guard generation automatically when opened in Unity on Linux — no manual patching needed.
9. **Build process**: Follow the [official Cesium developer setup](https://cesium.com/learn/cesium-unity/ref-doc/developer-setup.html), not the community Linux guide. Clone `cesium-unity-samples` as the Unity project (has all dependencies pre-configured), clone `cesium-unity` into its `Packages/`, publish Reinterop, open in Unity, cmake build. The community guide's extra steps (Reinterop.csproj patching, TilesetJsonLoader.cpp patching) are workarounds for older versions/specific environments and are not needed.
10. **Version: v1.15.3, not v1.15.4.** v1.15.4 bumped cesium-native to v0.45.0 which added `BoundingCylinderRegion` to the `BoundingVolume` variant, but cesium-unity v1.15.4 didn't update the `CalculateECEFCameraPosition` visitor to handle it — causing a compilation failure on any platform. The fix landed on main after v1.15.4 (commit `30502bd`). v1.15.3 pins cesium-native v0.44.x which doesn't have the new type. v1.15.4 had zero cesium-unity code changes over v1.15.3, so nothing is lost by staying on v1.15.3.

## Approach

An idempotent build script follows the [official Cesium developer setup](https://cesium.com/learn/cesium-unity/ref-doc/developer-setup.html): clone `cesium-unity-samples` (provides a complete Unity project with all dependencies), clone `cesium-unity` into its `Packages/`, publish Reinterop, open in Unity on Linux (triggers Reinterop code generation), then build native `.so` files with cmake. The build output is assembled into a fork package at `packages/unity/com.cesium.unity/` with Linux `.so` binaries. Outernet.Client manifest changes from Cesium registry to local `file:` path.

## Next step

Build script written (`scripts/build-cesium-native-linux.sh`), building v1.15.3. Waiting for cmake compilation to complete, then assemble the fork package and update Outernet.Client manifest.

## Done when

- [ ] Outernet.Client passes `uv run build-unity` for `linux64` (standalone player build) and `android` (compilation check)
- [ ] Forked `com.cesium.unity` package committed to repo with Linux binaries
- [ ] Outernet.Client manifest points at local fork
- [ ] Build process documented for future version bumps
- [ ] Follow-up ticket exists for CI build + registry hosting
- [ ] Play Mode can be entered without crashes (stretch goal, may surface separate blockers)
