---
id: T62
title: Unity headless batch builds in COI container
status: in-progress
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

**Reopened (1)** — `xvfb-run: error: Xvfb failed to start` during `coi build custom` (image build). Fixed by dropping `xvfb-run` and relying on `--headless` alone (750fcc92).

**Reopened (2)** — `unityhub --no-sandbox --headless install-path --set /opt/unity` segfaults (exit 139) during `coi build custom`. Crashpad error precedes: `elf_dynamic_array_reader.h:64: tag not found`. The same commands worked when run interactively in a fully launched COI container — the difference is the COI build container, which is a temporary container with likely more restricted environment (missing `/dev/shm`, tighter seccomp/AppArmor, missing pseudo-filesystems that Electron/Chromium needs). Unity Hub is an Electron app, so it's sensitive to these restrictions even in `--headless --no-sandbox` mode.

**Reopened (3)** — `ELECTRON_DISABLE_CRASHPAD=1` fix (fc511baf) did not resolve the segfault. Logs at `setup-agent-sandbox.log` from second `--rebuild` attempt confirm the crashpad error line still appears and the segfault still occurs on the same `unityhub install-path --set` call. The env var only controls the crash *reporter*, not the underlying Chromium subsystem that's segfaulting. The real issue is that Electron/Chromium probes ELF dynamic arrays at startup and hits a code path that dereferences invalid memory in the restricted build container. Possible next approaches:
- Bypass Unity Hub entirely: download the editor tarball via direct URL (avoids the Electron dependency in the build container altogether).
- Investigate what the COI build container is missing vs a running container (`/dev/shm`, `/proc` entries, seccomp profile) and pass flags to `coi build custom` to relax restrictions.
- Use `xvfb-run` + a virtual display (Reopened 1 showed Xvfb itself failed to start — may also be a build-container restriction).

## Observations

- `basedpyright` is not in the dev dependency group, so `uv run basedpyright` fails in the sandbox. Tracked as T63.
