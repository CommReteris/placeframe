---
id: T69
title: Build Cesium for Unity native plugin for Linux
status: plan-needed
depends_on: []
---

# T69: Build Cesium for Unity native plugin for Linux

## Goal

Get Outernet.Client's Cesium dependency compiling and entering Play Mode on Linux, so `uv run check-unity` passes for that project.

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

## Done when

- [ ] Outernet.Client passes `uv run check-unity` for both `android` and `linux64` targets
- [ ] Forked `com.cesium.unity` package committed to repo with Linux binaries
- [ ] Outernet.Client manifest points at local fork
- [ ] Build process documented for future version bumps
- [ ] Follow-up ticket exists for CI build + registry hosting
- [ ] Play Mode can be entered without crashes (stretch goal, may surface separate blockers)
