---
id: T75
title: "Win64 CI: enable IL2CPP builds"
status: design-needed
depends_on: [T7]
---

# T75: Win64 CI: enable IL2CPP builds

## Goal

Enable the two commented-out win64 builds (Outernet.Client, MapRegistrationTool) in `unity.yml` using IL2CPP scripting backend.

## Context

T7 implements the Unity CI workflow with all 7 builds running on Linux using GameCI Docker images. The two win64 builds are commented out because IL2CPP for Windows cannot be cross-compiled from Linux — there is no `windows-il2cpp` module for the Linux Unity editor. Only `windows-mono` exists, and the projects require IL2CPP. A Windows environment is strictly required.

Additionally, IL2CPP on Windows requires MSVC (`cl.exe` from Visual Studio Build Tools). This is a Unity-specific requirement — other C++ compilers (MinGW, Clang) are not supported. Microsoft's licensing prohibits *publicly* redistributing VS Build Tools inside Docker images — but building private images with VS Build Tools installed is explicitly supported and documented by Microsoft ([Install VS Build Tools into a container](https://learn.microsoft.com/en-us/visualstudio/install/build-tools-container?view=vs-2022)). This is why GameCI can't include them in their public images, but we can build our own private image.

Our current workflow uses only GameCI's Docker images (not their GitHub Actions). Activation, build, and license return are handled directly via `unity-editor` CLI and `uv run build-unity`.

## Key files

- `.github/workflows/unity.yml` — add win64 builds
- `scripts/src/scripts/build_unity.py` — may need path adjustments for Windows Unity install location

## Research

- `agent/research/unity-ci-licensing.md` — licensing seat analysis: why Linux parallel builds work (hardcoded `machine-id`), why Windows is different, machine fingerprinting on Windows, HardwareId test proposal
- `agent/research/win64-il2cpp-ci-approaches.md` — cross-compilation infeasibility, MSVC requirement, evaluation of all approaches (serialize + native install, Windows Docker, self-hosted runner, managed runners, skip)
- Session research (2026-03-04, not yet written to file):
  - **Windows containers on hosted runners**: 25-40 min pull (no layer cache), 33 GB disk on WS2025, `container:` job syntax Linux-only. Fatal for hosted, solved by self-hosted.
  - **Unity in Windows containers**: GameCI solved the Server Core DLL issue (copy opengl32.dll etc from full Windows image). Unity Hub and Editor batchmode work in their Windows images. IL2CPP specifically (needs VS) is unproven but plausible.
  - **VS Build Tools in containers**: MS official Dockerfile pattern works. Minimal workload: `VCTools --includeRecommended` (~15 GB). vswhere default scope excludes Build Tools — needs `-products *`.
  - **Self-hosted runner hosting**: Hetzner AX41 + WS2022 ~€65-70/mo best value; spare machine is free. Public repo = no GitHub platform fee.

### Licensing situation

Unity Personal allows 2 activation seats. Current usage: 1 seat for the dev machine, 1 seat for all Linux CI (GameCI containers share a hardcoded `/etc/machine-id`, so Unity sees them as one machine). Windows builds must share the remaining seat, which means all of CI (Linux + Windows) shares 1 seat. Windows builds must run after Linux builds finish, not just after each other. Concurrent workflows (push to main + dev simultaneously) also need coordination — a GitHub `concurrency` group would queue Windows activation across workflows.

If a runner crashes mid-build, the license isn't returned (recoverable via Unity ID portal, but manual).

### Approaches evaluated

| Approach | Install overhead | Licensing | Cost | Risk |
|---|---|---|---|---|
| **Serialize + native install** | 10-20 min cold, 3-8 min cached (5-7 GB eats most of 10 GB cache budget) | Serialize all Windows after Linux + concurrency group across workflows | $0 | Low — slow but reliable |
| ~~**Windows Docker + VS mount**~~ | None (Unity in image) | Custom image could hardcode identity (partial — registry yes, SMBIOS no) | $0 | High — VS mount fragile, DNS/IPC issues reported |
| **Private Windows Docker image (Unity + VS Build Tools baked in)** | None (everything in image) | Custom image can hardcode registry-based identity; SMBIOS still uncontrolled | $0 | Medium — needs research on Windows container support on `windows-latest` |
| **Self-hosted runner** | None (permanent install) | 1 consistent seat | $0 + hardware | Medium — maintenance burden |
| **Managed runners (Buildalon)** | None (persistent VMs) | Handled | $40-180/mo | Medium — single-person project, governance risk |
| **GitHub custom images** | None (baked in) | Depends on approach | Requires Team/Enterprise plan | Low-Medium |
| **Mono backend for win64** | None (cross-compiles from Linux GameCI) | Same as Linux (shared `machine-id`) | $0 | Low — no documented Mono issues for win64; projects just have IL2CPP set in PlayerSettings |
| **Skip win64 CI** | N/A | N/A | $0 | Accept the gap |

### Untested assumption: shared HardwareId on `windows-latest`

If GitHub's hosted Windows runners share the same machine identity signals that Unity licensing checks (likely the Windows Product ID), then native-runner activation would consume only 1 seat — the same trick that works on Linux, but via Azure's VM provisioning rather than a hardcoded container ID. This would make serialization simpler (no cross-workflow seat conflicts, parallel Windows builds safe). A test workflow dumping WMI values across parallel jobs would confirm or rule this out. See licensing research doc section 5 for the proposed test.

## Design decisions

1. **Two separate jobs** (not conditional matrix). The `build-linux` job uses GameCI Linux containers; `build-windows` uses a self-hosted Windows runner. Clean separation, no conditional YAML.
2. ~~**GameCI `windows-il2cpp` containers**~~ — Withdrawn. GameCI Windows Docker containers require mounting VS Build Tools from the host (fragile path coupling), don't hardcode machine-id (licensing issues), and have known DNS/IPC bugs. Not viable.
3. **VS Build Tools licensing is not a blocker for private images.** Microsoft's restriction is on *public redistribution* only. Building a private Docker image with VS Build Tools baked in for your own CI is explicitly supported ([MS docs](https://learn.microsoft.com/en-us/visualstudio/install/build-tools-container?view=vs-2022)). This reopens the containerized Windows build approach — build our own image with Unity + VS Build Tools, push to a private registry (GHCR).
4. **Self-hosted runner + private Docker image.** GitHub-hosted `windows-latest` is not viable for containerized builds: no persistent Docker layer cache (25-40 min pull every run), only 33 GB disk (WS2025), and 2 vCPUs (too slow for IL2CPP compilation). A self-hosted Windows runner solves all three: Docker cache persists between runs, disk/CPU are user-controlled. The private image (Unity + VS Build Tools baked in) on GHCR gives the same container reproducibility as the Linux GameCI approach.
5. **Hosted runners rejected for containers, not for native install.** The research showed that native Unity install + `actions/cache` on `windows-latest` (Option B) is viable as a fallback if self-hosted proves too burdensome. But containers on hosted runners are economically backwards — pull time exceeds native install time.
6. **Public repo = no GitHub platform fee.** Self-hosted runner usage on public repos remains free (no $0.002/min orchestration charge introduced March 2026).

## Next step

**Plan the self-hosted runner + private Docker image approach.** Research validated that self-hosted eliminates the three blockers that made containers unviable on hosted runners (pull time, disk, CPU). Open questions before planning:

1. **vswhere discovery** — Does Unity 6 pass `-products *` to `vswhere.exe`, allowing it to find VS Build Tools (not just full VS)? If not, what's the workaround (env var, registry key, symlink)?
2. **Machine identity inside Windows containers** — Can we hardcode registry-based identity signals (Windows Product ID) to get the same licensing trick as Linux's hardcoded `machine-id`? Or does the self-hosted runner's consistent machine identity make this moot (container activation vs host activation)?
3. **Image build pipeline** — Build the Windows Docker image on the self-hosted runner itself? Or in a GitHub Actions workflow on `windows-2022`? How often to rebuild?
4. **Runner provisioning** — Hardware selection, OS setup, Docker configuration, GitHub runner registration. Document as a reproducible setup script (like `setup-agent-sandbox` for COI).
5. **Disk space on `windows-latest`** — Revisit whether 33 GB on WS2025 hosted runners is workable for any part of the workflow (e.g., image build step only, with builds on self-hosted).

## Done when

- win64 matrix entries build successfully with IL2CPP scripting backend
- Windows builds run on a Windows environment (runner or container)
- All other builds remain unchanged on Linux/GameCI
