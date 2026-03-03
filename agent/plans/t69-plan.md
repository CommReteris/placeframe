# T69 Plan: Build Cesium for Unity Native Plugin for Linux

## Context

`com.cesium.unity` v1.15.4 ships no Linux native binaries and all generated C# interop code is wrapped in `#if UNITY_EDITOR_WIN` / `#if UNITY_EDITOR_OSX` guards (no Linux equivalent). On Linux, the interop layer compiles out entirely, causing CS0246 errors that make `uv run build-unity` fail. Additionally, `CesiumRuntime.asmdef` has `includePlatforms` without `LinuxStandalone64`, excluding the assembly from standalone Linux builds.

## Approach

A single idempotent build script follows the [community Linux guide](https://github.com/JOHNI1/CesiumSetupLinuxGuide) to build the entire package from source. Opening the cesium-unity project in Unity on Linux triggers the Reinterop source generator, which automatically produces both the C# interop code (with `#if UNITY_EDITOR_LINUX` guards) and the C++ interop code. The native C++ library is then built with cmake/vcpkg. The build output — Linux C# code, `.so` binaries, and updated asmdef — is assembled into a fork package committed to the repo.

No manual C# patching is needed. The Reinterop source generator handles Linux guard generation as part of the normal build process.

### Step 1: Write the idempotent build script

**File**: `scripts/build-cesium-native-linux.sh`

An idempotent bash script that works from any container state. Each step checks whether it's already done before executing:

1. **Install build dependencies** — `cmake`, `ninja-build`, `nasm`, `dotnet-sdk-8.0` (Microsoft APT repo), `g++` — each checked via `command -v` before installing
2. **Clone cesium-unity** to `$BUILD_DIR/cesium-unity` at tag `v1.15.4` with `--recurse-submodules` — skipped if directory exists
3. **Publish Reinterop** — `dotnet publish Reinterop~ -o .` — produces the Roslyn source generator DLL
4. **Open in Unity on Linux** — `xvfb-run /opt/unity/.../Unity -batchmode -nographics -quit -projectPath $BUILD_DIR/cesium-unity` — triggers Reinterop to generate both C# (with Linux guards) and C++ interop code. Expect DllNotFoundException warnings (no native library yet) but code generation still completes.
5. **Update CesiumRuntime.asmdef** — add `"LinuxStandalone64"` to `includePlatforms`
6. **Apply patches** — TilesetJsonLoader.cpp patch if needed (community guide mentions this for v1.15.3)
7. **Build Runtime .so** — `cmake` + `cmake --build` with `-DEDITOR=OFF`, vcpkg triplet `x64-linux-unity`
8. **Build Editor .so** — same with `-DEDITOR=ON`
9. **Copy outputs** — `.so` files and the generated C# files (with Linux guards) to a specified output directory

Script takes `BUILD_DIR` and `OUTPUT_DIR` as arguments with sensible defaults.

### Step 2: Assemble the fork package

After the build script completes, assemble the fork package at `packages/unity/com.cesium.unity/`:

- Copy the non-binary files from the official cached package (C# source, .meta, .asmdef, package.json, Tests/) — these provide the existing platform support
- Copy the Linux-generated C# files from the build output (the Reinterop-generated files with `#if UNITY_EDITOR_LINUX` / `#if UNITY_STANDALONE_LINUX` guards) — these replace the official generated files with a superset that includes Linux
- Copy the Linux `.so` files from the build output
- Update `CesiumRuntime.asmdef` to include `LinuxStandalone64`
- Update `package.json` version to `1.15.4-linux.1`
- No other platform native binaries (saves ~1.3GB)
- `.meta` files for the `.so` binaries are generated automatically by Unity on first import

### Step 3: Update Outernet.Client manifest

In `legacy/Outernet.Client/Packages/manifest.json`:
- Change `"com.cesium.unity": "1.15.4"` to `"com.cesium.unity": "file:../../../packages/unity/com.cesium.unity"`
- Keep the Cesium scoped registry entry (harmless, makes reverting easier)

### Step 4: Add .gitattributes entry

Add `packages/unity/com.cesium.unity/**/*.so binary` to `.gitattributes` to prevent line-ending conversion.

## Key files

| File | Action |
|---|---|
| `scripts/build-cesium-native-linux.sh` | Create (~150 lines, idempotent build script) |
| `packages/unity/com.cesium.unity/` | Create (fork directory: C# from cache + Linux C# and .so from build) |
| `packages/unity/com.cesium.unity/Runtime/CesiumRuntime.asmdef` | Modify (add LinuxStandalone64) |
| `packages/unity/com.cesium.unity/package.json` | Modify (version + displayName) |
| `legacy/Outernet.Client/Packages/manifest.json` | Modify (file: path) |
| `.gitattributes` | Modify (binary marker for .so) |

## Risks

1. **Unity compilation warnings during code generation** — Opening cesium-unity in Unity on Linux will produce DllNotFoundException since no native library exists yet. Per the community guide, this is expected — Reinterop still generates the code. If compilation fails hard (preventing code generation), the asmdef may need updating before the Unity step.
2. **TilesetJsonLoader.cpp patch** — The v1.15.3 community guide mentions a patch. May or may not be needed for v1.15.4. Build script attempts clean build first, applies patch only if needed.
3. **vcpkg build time** — First run: 30-60 minutes for dependency compilation. Script is idempotent so subsequent runs are fast.
4. **Binary size** — Linux .so files ~50-65MB. Committed temporarily; T70 moves to CI + registry.

## Verification

1. `uv run build-unity --project Outernet.Client --target linux64` — must pass (actual standalone player build, exercises .so linkage)
2. `uv run build-unity --project Outernet.Client --target android` — must still pass (compilation check only, no Android toolchain available)
3. Verify fork package has Linux .so files at expected paths
4. Spot-check generated C# files for `#if UNITY_EDITOR_LINUX` guards (produced by Reinterop, not manual patching)
