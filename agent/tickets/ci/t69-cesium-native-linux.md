---
id: T69
title: Build Cesium for Unity native plugin for Linux
status: design-needed
depends_on: []
---

# T69: Build Cesium for Unity native plugin for Linux

## Goal

Get Outernet.Client's Cesium dependency compiling and entering Play Mode on Linux, so `uv run check-unity` passes for that project.

## Context

`com.cesium.unity` v1.15.4 ships native binaries for Windows, macOS, Android, iOS, and UWP — but not Linux. The generated C# interop layer is wrapped in `#if UNITY_EDITOR_WIN` / `#if UNITY_EDITOR_OSX` guards with no `#if UNITY_EDITOR_LINUX` block, so the entire Reinterop layer compiles out on Linux, producing CS0246 errors for `ReinteropNativeImplementation`.

There is no official Linux support and no indication it's on the roadmap (GitHub issue [#513](https://github.com/CesiumGS/cesium-unity/issues/513)). A community guide exists for v1.15.3: [JOHNI1/CesiumSetupLinuxGuide](https://github.com/JOHNI1/CesiumSetupLinuxGuide).

Research report: `agent/research/cesium-unity-native-linux.md`

## Open questions

1. **Artifact hosting**: The build produces `.so` files (~50-100 MB). Options: git URL package, local file path in repo, local tarball, or self-hosted Verdaccio registry. The other platforms use Cesium's hosted UPM registry. What's the right approach for one custom package?
2. **Augment vs. replace**: Building for Linux produces a superset of the official package (existing platform binaries + Linux `.so` + Linux-guarded generated C#). Should this replace `com.cesium.unity` in the manifest, or supplement it?
3. **Build location**: Should the `.so` be baked into the COI image at image build time (like the Unity editor), or built separately and stored somewhere else?
4. **Play Mode testing**: The bar is Play Mode, not just compilation. Cesium-native has no GPU dependency (it's a data processing library), but Unity MonoBehaviours touching the rendering pipeline might not handle the Null Graphics Device gracefully. Is "loads without crashing" sufficient, or do we need specific Cesium functionality working?
5. **Version tracking**: When Cesium releases a new version, how do we rebuild? Manual process, or automated?

## Done when

- [ ] Outernet.Client passes `uv run check-unity` for both `android` and `linux64` targets
- [ ] Cesium native `.so` is hosted in a persistent, reproducible location
- [ ] Build process is documented (or scripted) for future version bumps
- [ ] Play Mode can be entered without crashes (stretch goal, may surface separate blockers)
