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

Research reports:
- `agent/research/unity-headless-batch-builds.md` (original feasibility research)
- `agent/research/unity-hub-segfault-in-coi-build.md` (segfault root cause + direct download approach)

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

**Revised**: bypass Unity Hub in the build script entirely. Download the editor and modules via direct URLs from Unity's CDN, avoiding the Electron dependency that segfaults in the COI build container. Unity publishes a per-version `.ini` manifest at `https://download.unity3d.com/download_unity/{changeset}/unity-{version}-linux.ini` with all download URLs and checksums.

Key downloads for 6000.0.66f1 (changeset `e7adf66625be`):
- Editor: `LinuxEditorInstaller/Unity.tar.xz` (4.5 GB, tar.xz)
- Linux IL2CPP: `LinuxEditorTargetInstaller/UnitySetup-Linux-IL2CPP-Support-for-Editor-6000.0.66f1.tar.xz` (66 MB, tar.xz)
- Android support: `MacEditorTargetInstaller/UnitySetup-Android-Support-for-Editor-6000.0.66f1.pkg` (675 MB, needs `7z`/`cpio` extraction — no Linux-native `.tar.xz` available)
- Android SDK/NDK/JDK: individual downloads from Google + Unity CDN (see research report)

Mount the host `.ulf` license via an Incus profile disk device added by `setup_agent_sandbox.py`. Provide `uv run check-unity` to run compilation checks. See `agent/plans/t62-plan.md` for original plan; approach updated per `agent/research/unity-hub-segfault-in-coi-build.md`.

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

**Reopened (3)** — `ELECTRON_DISABLE_CRASHPAD=1` fix (fc511baf) did not resolve the segfault. Research (`agent/research/unity-hub-segfault-in-coi-build.md`) identified the root cause: Chromium's GPU process crashes in the containerized environment, Crashpad's ptrace broker tries to snapshot the crash but fails due to Yama ptrace_scope restrictions in the container's PID namespace, producing a secondary segfault. The `ELECTRON_DISABLE_CRASHPAD=1` env var is undocumented and may not be respected by Unity Hub 3.16.3's Electron build. COI source code review confirmed the build container and running container have **identical security configs** — the "works in running container" observation suggests the issue is timing (services not fully initialized) rather than missing capabilities. **Decision: abandon Unity Hub in the build script. Switch to direct downloads from Unity's CDN.** The `.ini` manifest at `download.unity3d.com` provides all URLs and checksums. Editor and Linux modules are `.tar.xz`; Android module requires `.pkg` extraction via `7z`/`cpio`.

**Reopened (3) fix** — Rewrote `coi-placeframe-build.sh` to use direct downloads from Unity's CDN. Tested `.pkg` extraction in-container: the Apple xar archive contains a plain cpio `Payload~` (not gzipped), which extracts flat to the `AndroidPlayer/` level. Editor and Linux IL2CPP are straightforward `tar xJ` extractions. Android SDK/NDK/JDK downloaded individually from Google/Unity CDN with directory renames to match Unity's expected layout. Skipped `modules.json` creation — will add if Unity can't auto-discover modules during compilation checks.

**Reopened (4)** — `curl: (22) The requested URL returned error: 404` during OpenJDK download in `coi-placeframe-build.sh`. The build script constructs the URL as `$CDN/open-jdk/open-jdk-linux-x64/jdk17.0.9-9_...zip` where `CDN=https://download.unity3d.com/download_unity/$CHANGESET`. This expands to `download_unity/e7adf66625be/open-jdk/...` — but Unity hosts OpenJDK at a **version-independent** path without the changeset prefix: `download_unity/open-jdk/open-jdk-linux-x64/...`. Confirmed via HEAD requests: the changeset-prefixed URL returns 404, the root-level URL returns 200. The Unity release API (`services.api.unity.com/unity/editor/release/v1/releases`) confirms the correct URL has no changeset prefix. **Fix:** use the absolute URL `https://download.unity3d.com/download_unity/open-jdk/open-jdk-linux-x64/jdk17.0.9-9_8d1cbcce56285f3146cf7761353a643fe573b39e45bd94f35590dca39277f667.zip` instead of `$CDN/open-jdk/...`. The `.ini` manifest doesn't list the JDK at all — it's only discoverable via the release API.

## Observations

- `basedpyright` is not in the dev dependency group, so `uv run basedpyright` fails in the sandbox. Tracked as T63.
