---
id: T7
title: Unity CI workflow
status: plan-needed
depends_on: [T4]
---

# T7: Unity CI workflow

See `ci-background.md` for shared CI context.

## Goal

Automated Unity builds in CI for the full build matrix, running on every push to `main` and `dev` and on PRs targeting those branches.

## Context

Placeframe includes three active Unity projects targeting multiple platforms. All use Unity 6 LTS (6000.0.66f1).

Foundation work is complete:
- **T62** established `uv run build-unity`, direct Unity CDN installation, and serial-based license activation in the COI sandbox.
- **T69** built the Cesium native Linux plugin (committed at `packages/unity/com.cesium.unity/`).
- **T73** fixed `-quit` so batchmode builds exit cleanly.

### Build matrix

| Project | android-mobile | magicleap | linux64 | win64 |
|---|---|---|---|---|
| **Outernet.Client** | yes | yes | yes | yes |
| **MapRegistrationTool** | - | - | yes | yes |
| **AndroidMobile** | yes | - | - | - |

7 total builds across 3 projects.

## Key files

- `scripts/src/scripts/build_unity.py` — build script (needs platform enum, `-executeMethod` support, Windows)
- `legacy/Outernet.Client/Assets/OuternetClient/Editor/BuildScript.cs` — Android/ML2 configure+build methods
- `apps/AndroidMobile/` — needs a `BuildScript.cs` added (currently has none)
- `agent/coi-placeframe-build.sh` — Unity installation reference
- `.github/workflows/build.yml` — existing Docker build workflow (patterns)
- `packages/generated/csharp/` — generated C# API client consumed by Unity

## Design decisions

1. **GameCI hybrid approach.** Use GameCI's Docker images (`unityci/editor`) for the pre-built Unity environment. Use GameCI's activation action (`game-ci/unity-activate`) for license management. Call `uv run build-unity` for actual build logic (keeps it in Python, portable, tested locally). Don't use `game-ci/unity-builder` — our build script handles the Unity CLI.
2. **License: serial-based activation** via GameCI's activation action, credentials in GitHub Secrets. ULF copy doesn't work with Unity 6 headless (learned in T62).
3. **C# API client: assume committed is current.** Enforces that developers regenerate before pushing. No need to run the API service in Unity CI.
4. **Trigger strategy: pushes to `main` and `dev`, PRs targeting both.** T4 establishes the multi-branch CI pattern.
5. **Platform enum in `build_unity.py`.** The script defines a flat enumeration of platforms: `android-mobile`, `magicleap`, `linux64`, `win64`. The `--platform` parameter is the only input — the script does the right thing for each platform (CLI flags for standalone, `-executeMethod` for Android sub-platforms). No separate `--target` / `--variant` split.
6. **`-executeMethod` for Android sub-platforms.** Android Mobile and Magic Leap 2 are both `BuildTarget.Android` but need different XR loaders, graphics APIs, architectures, texture compression, and scripting defines. The existing C# `BuildScript.cs` methods (`ConfigureForMagicLeap()` + `BuildForMagicLeap()`, etc.) handle this. The Python script calls them via `-executeMethod`. A `BuildScript.cs` must be added to the AndroidMobile app (currently has none).
7. **Standalone builds use `AUTHORING_TOOLS_ENABLED`.** Already set in Outernet.Client's `ProjectSettings.asset` for Standalone. MapRegistrationTool will need the same.
8. **Windows runner for Windows standalone.** Linux runners can't produce Windows builds. CI uses a Windows runner (`windows-latest`) for `win64` targets.
9. **One job per build, fully parallel.** All 7 builds run as separate parallel jobs. Each job restores its Library cache independently. This gives the best wall-clock time and per-build status granularity. Library cache keys are scoped per project (the cache is platform-independent — it's asset import results).

## Depends on

T4 (branch-based builds) — establishes multi-branch triggers and `.env.lock` commit strategy that T7's workflow must follow.

## Done when

**Verifiable now (no special infra):**
- Workflow file `.github/workflows/unity.yml` exists and is syntactically valid
- `build_unity.py` supports the full platform enum (`android-mobile`, `magicleap`, `linux64`, `win64`)
- `BuildScript.cs` exists in AndroidMobile app

**Requires GitHub Actions (verify manually):**
- Full build matrix passes on push to `main`
- License activation works reliably
- Library cache reduces subsequent build times
