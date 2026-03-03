---
id: T62
title: Unity headless batch builds in COI container
status: plan-needed
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

## Design decisions

1. **Image vs volume** → bake into image. Install editors in `coi-placeframe-build.sh` (~15-20 GB). Slower image rebuild on Unity version bumps, but fast container launch and no first-run surprises.
2. **License file management** → Incus profile mount. `setup_agent_sandbox.py` locates `~/.local/share/unity3d/Unity/Unity_lic.ulf` on the host and adds a read-only profile disk device mounting it into the container. Errors out if the `.ulf` is missing. Same pattern as git identity — host credential material lives in the profile, not the image. Auto-updates if the user re-activates locally.
3. **Compilation wrapper** → `uv run` command (e.g. `uv run check-unity`). Follows existing pattern (`uv run up`, `uv run build`, etc.). Runnable from repo root, no Claude Code dependency.

## Key risks

- **`.ulf` fingerprint mismatch**: Unity Personal `.ulf` contains a machine fingerprint. In practice, GameCI relies on this working across different CI machines and it has for years, but it's an undocumented tolerance. Incus system containers share the host kernel and CPU identity, so risk is lower than Docker. **Smoke-test this early** before investing in the full installation.

## Approach (high level)

1. Extend `setup_agent_sandbox.py` to find the host `.ulf` and add an Incus profile disk device mounting it read-only at the container's Unity license path. Error if not found.
2. Extend `agent/coi-placeframe-build.sh` to install xvfb, X11/Mesa system dependencies, and Unity Hub CLI.
3. Install both editor versions with `android`, `android-sdk-ndk-tools`, `android-open-jdk`, and `linux-il2cpp` modules.
4. Smoke-test: verify Unity launches in batchmode and accepts the mounted `.ulf` license.
5. Add a compilation check wrapper that runs `xvfb-run Unity -batchmode -nographics -quit -projectPath <path> -buildTarget <target>` and reports success/failure.
6. Verify all four projects compile for both Android and Linux Standalone targets.

## Done when

- [ ] Both Unity editors installed and launchable in batchmode inside COI container
- [ ] License activation works (Personal `.ulf` approach)
- [ ] All four projects pass compilation check for Android target
- [ ] All four projects pass compilation check for Linux Standalone target
- [ ] Compilation check is runnable as a command from repo root
