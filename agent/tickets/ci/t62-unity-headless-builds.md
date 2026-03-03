---
id: T62
title: Unity headless batch builds in COI container
status: ready
depends_on: []
plan: t62-plan.md
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
2. **License file management** → Incus profile mount. `setup_agent_sandbox.py` locates `~/.local/share/unity3d/Unity/Unity_lic.ulf` on the host and adds a read-only profile disk device mounting it into the container. **Fatal error** if the `.ulf` is missing — the COI image includes Unity, so a license is required. Same pattern as git identity — host credential material lives in the profile, not the image. Auto-updates if the user re-activates locally.
3. **Compilation wrapper** → `uv run` command (e.g. `uv run check-unity`). Follows existing pattern (`uv run up`, `uv run build`, etc.). Runnable from repo root, no Claude Code dependency.

## Key risks

- **`.ulf` fingerprint mismatch**: Unity Personal `.ulf` contains a machine fingerprint. In practice, GameCI relies on this working across different CI machines and it has for years, but it's an undocumented tolerance. Incus system containers share the host kernel and CPU identity, so risk is lower than Docker. **Smoke-test this early** before investing in the full installation.

## Approach

Bake Unity 6000.0.66f1 (the version all four projects currently use) into the COI image via `coi-placeframe-build.sh`. Mount the host `.ulf` license via an Incus profile disk device added by `setup_agent_sandbox.py`. Provide `uv run check-unity` to run compilation checks — it reads each project's `ProjectVersion.txt` at runtime, so when the 2022.3 downgrade happens, only the image needs a second editor install. See `agent/plans/t62-plan.md` for full detail.

## Done when

- [ ] Both Unity editors installed and launchable in batchmode inside COI container
- [ ] License activation works (Personal `.ulf` approach)
- [ ] All four projects pass compilation check for Android target
- [ ] All four projects pass compilation check for Linux Standalone target
- [ ] Compilation check is runnable as a command from repo root

## Log

Clean implementation, no issues. Basedpyright not available in sandbox (tracked as T63), so type checking was done via `npx basedpyright` — all errors are pre-existing import resolution failures, not new issues.

**Reopened** — `xvfb-run: error: Xvfb failed to start` during `coi build custom` (image build). Xvfb installs fine (line 28) but can't start inside the Incus build container — likely missing `/tmp/.X11-unix`, security restrictions, or no `/dev/shm`. The unityhub postinst script already ran `unityhub` successfully without Xvfb (output shows `All Unity Editors will be installed to /opt/unity`), so `--headless` may be sufficient without `xvfb-run`. Fix options: (1) drop `xvfb-run` and rely on `--headless` alone, (2) create `/tmp/.X11-unix` and ensure `xauth` is present before the xvfb-run calls.

## Observations

- `basedpyright` is not in the dev dependency group, so `uv run basedpyright` fails in the sandbox. Tracked as T63.
