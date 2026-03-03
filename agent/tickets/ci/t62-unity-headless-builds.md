---
id: T62
title: Unity headless batch builds in COI container
status: design-needed
depends_on: []
---

# T62: Unity headless batch builds in COI container

## Goal

Enable compilation verification for the four Unity projects (AndroidMobile, MapRegistrationTool, MakeItSing, Outernet.Client) inside the COI sandbox, targeting Android and Linux Standalone.

## Context

Research report: `agent/research/unity-headless-batch-builds.md`

Claude Code currently cannot verify that Unity C# code compiles. When editing generated API clients or Placeframe packages consumed by the Unity projects, there is no feedback loop — breakage is only discovered when a human opens the project in the Unity Editor.

Two editor versions are needed:
- **Unity 2022.3 LTS** — AndroidMobile, MapRegistrationTool, MakeItSing (downgrade from Unity 6 pending)
- **Unity 6 LTS (6000.0.66f1)** — legacy/Outernet.Client

## Key decisions needed

1. **Image vs volume**: install editors in `coi-placeframe-build.sh` (baked into image, ~15-20 GB) or into a persistent Incus volume (smaller image, first-launch delay)?
2. **License file management**: where to store the `.ulf` — baked into image, mounted at runtime, or fetched from a secret store?
3. **Compilation wrapper**: standalone script, uv command, or skill?
4. **Unity 2022.3 specific version**: which 2022.3.XXf1 patch to target?

## Approach (high level)

1. Extend `agent/coi-placeframe-build.sh` to install xvfb, X11/Mesa system dependencies, and Unity Hub CLI.
2. Install both editor versions with `android`, `android-sdk-ndk-tools`, `android-open-jdk`, and `linux-il2cpp` modules.
3. Copy a locally-activated Personal `.ulf` license file into the container.
4. Add a compilation check wrapper that runs `xvfb-run Unity -batchmode -nographics -quit -projectPath <path> -buildTarget <target>` and reports success/failure.
5. Verify all four projects compile for both Android and Linux Standalone targets.

## Done when

- [ ] Both Unity editors installed and launchable in batchmode inside COI container
- [ ] License activation works (Personal `.ulf` approach)
- [ ] All four projects pass compilation check for Android target
- [ ] All four projects pass compilation check for Linux Standalone target
- [ ] Compilation check is runnable as a command from repo root
