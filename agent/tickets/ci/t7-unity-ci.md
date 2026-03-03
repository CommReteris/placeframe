---
id: T7
title: Unity CI workflow
status: design-needed
depends_on: [T4]
---

# T7: Unity CI workflow

See `ci-background.md` for shared CI context.

## Goal

Automated Unity compilation checks and player builds in CI for the full build matrix, running on every push to `main` and `dev` and on PRs targeting those branches.

## Context

Placeframe includes three active Unity projects targeting multiple platforms. All use Unity 6 LTS (6000.0.66f1).

Foundation work is complete:
- **T62** established `uv run build-unity`, direct Unity CDN installation, and serial-based license activation in the COI sandbox.
- **T69** built the Cesium native Linux plugin (committed at `packages/unity/com.cesium.unity/`).
- **T73** fixed `-quit` so batchmode builds exit cleanly.

### Build matrix

| Project | Android Mobile | Magic Leap 2 | Linux Standalone | Windows Standalone |
|---|---|---|---|---|
| **Outernet.Client** | yes | yes | yes | yes |
| **MapRegistrationTool** | - | - | yes | yes |
| **AndroidMobile** | yes | - | - | - |

- **Standalone builds** (Linux + Windows) must have `AUTHORING_TOOLS_ENABLED` in scripting defines. This is already set in Outernet.Client's `ProjectSettings.asset` for the Standalone platform. MapRegistrationTool will need the same.
- **Android Mobile** and **Magic Leap 2** must NOT have `AUTHORING_TOOLS_ENABLED`.
- **Android vs Magic Leap 2** are both `BuildTarget.Android` but require different XR loaders, graphics APIs, architectures, texture compression, and render pipeline assets. Existing `BuildScript.cs` files handle this via `ConfigureForMagicLeap()` and `ConfigureForAndroidMobile()` methods (see `legacy/Outernet.Client/Assets/OuternetClient/Editor/BuildScript.cs`).

### Platform configuration challenge

The current `build_unity.py` passes `-buildTarget android` or `-buildLinux64Player` but has no concept of sub-platforms (Android Mobile vs Magic Leap 2) or Windows standalone. For the full matrix, it needs to either:
- Call `-executeMethod Outernet.Client.Build.ConfigureForMagicLeap` (or `ConfigureForAndroidMobile`) before building, using the existing C# BuildScript methods
- Or replicate the configuration logic in the Python build script (fragile, duplicates C# code)

The `-executeMethod` approach is cleaner — it reuses the existing C# configuration and keeps platform-specific knowledge in Unity where it belongs.

Windows standalone builds require a Windows runner or cross-compilation support. Linux CI can only produce Linux standalone and Android builds natively.

## Key files

- `scripts/src/scripts/build_unity.py` — build script (needs sub-platform + Windows support)
- `legacy/Outernet.Client/Assets/OuternetClient/Editor/BuildScript.cs` — Android/ML2 platform configuration
- `agent/coi-placeframe-build.sh` — Unity installation reference
- `.github/workflows/build.yml` — existing Docker build workflow (patterns)
- `packages/generated/csharp/` — generated C# API client consumed by Unity

## Design decisions

1. **GameCI hybrid approach.** Use GameCI's Docker images (`unityci/editor`) for the pre-built Unity environment. Use GameCI's activation action (`game-ci/unity-activate`) for license management. Call `uv run build-unity` for actual build logic (keeps it in Python, portable, tested locally). Don't use `game-ci/unity-builder` — our build script handles the Unity CLI.
2. **License: serial-based activation** via GameCI's activation action, credentials in GitHub Secrets. ULF copy doesn't work with Unity 6 headless (learned in T62).
3. **C# API client: assume committed is current.** Enforces that developers regenerate before pushing. No need to run the API service in Unity CI.
4. **Trigger strategy: pushes to `main` and `dev`, PRs targeting both.** This requires T4 (branch-based builds) to land first — T4 establishes the multi-branch CI pattern.

## Open questions

1. **Windows standalone builds.** Linux runners can't produce Windows standalone. Options: (a) Windows runner for Windows builds, (b) skip Windows standalone in CI and only verify Linux standalone (standalone code paths are identical, only the binary differs), (c) cross-compile from Linux (Unity supports this for Mono backend but not IL2CPP). What's the right trade-off?
2. **Sub-platform support in build_unity.py.** The script needs a `--platform` or `--variant` flag to distinguish Android Mobile from Magic Leap 2. Should this use `-executeMethod` to call the existing C# configure methods, or should the Python script set scripting defines directly via CLI flags?
3. **Matrix parallelism.** 9 total builds (4 + 2 + 1 projects x platforms, minus combos that don't apply). Run as parallel jobs? Sequential steps? Each GameCI editor image pull is ~15GB.

## Depends on

T4 (branch-based builds) — establishes multi-branch triggers and `.env.lock` commit strategy that T7's workflow must follow.

## Done when

**Verifiable now (no special infra):**
- Workflow file `.github/workflows/unity.yml` exists and is syntactically valid
- `build_unity.py` supports the full build matrix (sub-platforms, Windows)

**Requires GitHub Actions (verify manually):**
- Full build matrix passes on push to `main`
- License activation works reliably
- Library cache reduces subsequent build times
