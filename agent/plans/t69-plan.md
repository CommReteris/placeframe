# T69 Plan: Build Cesium for Unity Native Plugin for Linux

## Context

`com.cesium.unity` v1.15.4 ships no Linux native binaries and all generated C# interop code is wrapped in `#if UNITY_EDITOR_WIN` / `#if UNITY_EDITOR_OSX` guards (no Linux equivalent). On Linux, the interop layer compiles out entirely, causing CS0246 errors that make `uv run check-unity` fail. Additionally, `CesiumRuntime.asmdef` has `includePlatforms` without `LinuxStandalone64`, excluding the assembly from standalone Linux builds.

## Approach

Two independent parts: **C# patching** (adds Linux platform guards — fixes compilation) and **native build** (produces Linux .so files — enables runtime). check-unity only checks compilation, so C# patching alone passes it, but the ticket requires Linux binaries committed too.

### Step 1: Create the fork package directory

Copy from the cached package at `Library/PackageCache/com.cesium.unity@AC303E3B95B5/` to `packages/unity/com.cesium.unity/`, stripping all non-Linux native binaries:

**Keep**: All C# source files, `.meta` files, `.asmdef` files, `package.json`, `Tests/`, shader files
**Delete**: `Editor/*.dll`, `Editor/*.dylib`, `Editor/arm64/`, `Editor/x86_64/`, `Plugins/Android/`, `Plugins/iOS/`, `Plugins/Standalone/*.dll`, `Plugins/Standalone/*.dylib`, `Plugins/WSA/`, and their `.meta` files

Result: ~20MB of C# code + configs (down from 1.4GB).

### Step 2: Add Linux C# guards to generated files

Write a Python script (`scripts/src/scripts/patch_cesium_linux_guards.py`) that mechanically adds Linux platform blocks to all 41 generated files in `*/generated/Reinterop.RoslynSourceGenerator/`:

- **Runtime generated files (30 files)**: Currently have 7 platform blocks. Add 2 more:
  - `#if UNITY_EDITOR_LINUX` (copy content from `UNITY_EDITOR_WIN` block — code is identical across all blocks)
  - `#if !UNITY_EDITOR && UNITY_STANDALONE_LINUX` (copy content from `UNITY_STANDALONE_WIN` block)

- **Editor generated files (11 files)**: Currently have 2 blocks. Add 1 more:
  - `#if UNITY_EDITOR_LINUX` (copy content from `UNITY_EDITOR_WIN` block)

The script extracts content between `#if GUARD` and its matching `#endif`, duplicates it with the Linux guard, and appends to the file. Reusable for future Cesium version bumps.

### Step 3: Update CesiumRuntime.asmdef

Add `"LinuxStandalone64"` to `includePlatforms` in `packages/unity/com.cesium.unity/Runtime/CesiumRuntime.asmdef`.

### Step 4: Update package.json

Change version to `"1.15.4-linux.1"` and displayName to `"Cesium for Unity (Linux fork)"` in the fork's `package.json`.

### Step 5: Write the idempotent native build script

**File**: `scripts/build-cesium-native-linux.sh`

An idempotent bash script that works from any container state. Each step checks whether it's already done before executing:

1. **Install build dependencies** — `cmake`, `ninja-build`, `nasm`, `dotnet-sdk-8.0` (Microsoft APT repo), `g++` — each checked via `command -v` before installing
2. **Clone cesium-unity** to `$BUILD_DIR/cesium-unity` at tag `v1.15.4` with `--recurse-submodules` — skipped if directory exists
3. **Patch clone's C# for Linux** — run the patching script on the clone (so Unity can compile it on Linux for the Reinterop code generation step)
4. **Publish Reinterop** — `dotnet publish Reinterop~ -o .` — produces the Roslyn source generator DLL
5. **Trigger C++ code generation via Unity** — `xvfb-run /opt/unity/.../Unity -batchmode -nographics -quit -projectPath $BUILD_DIR/cesium-unity` — Reinterop generates C++ interop headers at `native~/Runtime/generated-Editor/` and `native~/Editor/generated-Editor/`. **Risk**: these may already be committed in the repo; if so, skip this step. Verify by checking if the directory exists after clone.
6. **Build Runtime .so** — `cmake` + `cmake --build` with `-DEDITOR=OFF`, vcpkg triplet `x64-linux-unity`
7. **Build Editor .so** — same with `-DEDITOR=ON`
8. **Copy outputs** — `libCesiumForUnityNative-Runtime.so` and `libCesiumForUnityNative-Editor.so` to a specified output directory

Script takes `BUILD_DIR` and `OUTPUT_DIR` as arguments with sensible defaults (`/tmp/cesium-build`, `/tmp/cesium-output`).

### Step 6: Build and install .so files

Run the build script. Copy outputs into the fork package:
- `packages/unity/com.cesium.unity/Editor/libCesiumForUnityNative-Editor.so`
- `packages/unity/com.cesium.unity/Editor/libCesiumForUnityNative-Runtime.so` (editor loads the "Runtime" library too)
- `packages/unity/com.cesium.unity/Plugins/Standalone/libCesiumForUnityNative-Runtime.so`

Create `.meta` files for each with the Unity `PluginImporter` format (GUIDs generated, correct platform settings: Editor .so enabled for Editor/x86_64, Standalone .so enabled for LinuxUniversal).

### Step 7: Update Outernet.Client manifest

In `legacy/Outernet.Client/Packages/manifest.json`:
- Change `"com.cesium.unity": "1.15.4"` to `"com.cesium.unity": "file:../../../packages/unity/com.cesium.unity"`
- Keep the Cesium scoped registry entry (harmless, makes reverting easier)

### Step 8: Add .gitattributes entry

Add `packages/unity/com.cesium.unity/**/*.so binary` to `.gitattributes` to prevent line-ending conversion.

## Key files

| File | Action |
|---|---|
| `packages/unity/com.cesium.unity/` | Create (fork directory, ~20MB C# + .so files) |
| `packages/unity/com.cesium.unity/Runtime/generated/Reinterop.RoslynSourceGenerator/*.cs` (30) | Modify (add 2 Linux guard blocks each) |
| `packages/unity/com.cesium.unity/Editor/generated/Reinterop.RoslynSourceGenerator/*.cs` (11) | Modify (add 1 Linux guard block each) |
| `packages/unity/com.cesium.unity/Runtime/CesiumRuntime.asmdef` | Modify (add LinuxStandalone64) |
| `packages/unity/com.cesium.unity/package.json` | Modify (version + displayName) |
| `scripts/build-cesium-native-linux.sh` | Create (~150 lines) |
| `scripts/src/scripts/patch_cesium_linux_guards.py` | Create (~60 lines) |
| `legacy/Outernet.Client/Packages/manifest.json` | Modify (file: path) |
| `.gitattributes` | Modify (binary marker for .so) |

## Risks

1. **C++ code generation may need Unity** — The Reinterop source generator creates C++ headers needed by cmake. These may or may not be committed in the cesium-unity repo. The build script checks for their existence and only runs Unity if missing.
2. **TilesetJsonLoader.cpp patch** — The v1.15.3 community guide mentions a patch. May or may not be needed for v1.15.4. Build script attempts clean build first, applies patch only if needed.
3. **vcpkg build time** — First run: 30-60 minutes for dependency compilation. Script is idempotent so subsequent runs are fast.
4. **Binary size** — Linux .so files ~50-65MB. Committed temporarily; T70 moves to CI + registry.

## Verification

1. `uv run check-unity --project Outernet.Client --target linux64` — must pass
2. `uv run check-unity --project Outernet.Client --target android` — must still pass
3. Verify fork package has Linux .so files at expected paths
4. Spot-check a few generated C# files for correct Linux guards
