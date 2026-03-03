---
id: T69
title: Build Cesium for Unity native plugin for Linux
status: ready
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
8. **C# guard generation**: Reinterop source generator handles Linux C# guard generation automatically when opened in Unity on Linux — no manual patching needed. Following the [community Linux guide](https://github.com/JOHNI1/CesiumSetupLinuxGuide) build process.

## Approach

An idempotent build script follows the community Linux guide: clone cesium-unity, open in Unity on Linux (triggers Reinterop to generate C# with Linux guards + C++ interop code), build native `.so` files with cmake/vcpkg. The build output is assembled into a fork package at `packages/unity/com.cesium.unity/` — C# from the official cache augmented with Linux-generated C# and `.so` binaries, no other platform binaries (~100-150MB vs 1.4GB). Outernet.Client manifest changes from Cesium registry to local `file:` path.

## Done when

- [ ] Outernet.Client passes `uv run build-unity` for `linux64` (standalone player build) and `android` (compilation check)
- [ ] Forked `com.cesium.unity` package committed to repo with Linux binaries
- [ ] Outernet.Client manifest points at local fork
- [ ] Build process documented for future version bumps
- [ ] Follow-up ticket exists for CI build + registry hosting
- [ ] Play Mode can be entered without crashes (stretch goal, may surface separate blockers)
