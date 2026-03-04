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

Additionally, IL2CPP on Windows requires MSVC (`cl.exe` from Visual Studio Build Tools). This is a Unity-specific requirement — other C++ compilers (MinGW, Clang) are not supported. Microsoft's licensing prohibits redistributing VS Build Tools inside Docker images.

Our current workflow uses only GameCI's Docker images (not their GitHub Actions). Activation, build, and license return are handled directly via `unity-editor` CLI and `uv run build-unity`.

## Key files

- `.github/workflows/unity.yml` — add win64 builds
- `scripts/src/scripts/build_unity.py` — may need path adjustments for Windows Unity install location

## Research

- `agent/research/unity-ci-licensing.md` — licensing seat analysis: why Linux parallel builds work (hardcoded `machine-id`), why Windows is different, machine fingerprinting on Windows, HardwareId test proposal
- `agent/research/win64-il2cpp-ci-approaches.md` — cross-compilation infeasibility, MSVC requirement, evaluation of all approaches (serialize + native install, Windows Docker, self-hosted runner, managed runners, skip)

### Licensing situation

Unity Personal allows 2 activation seats. Current usage: 1 seat for the dev machine, 1 seat for all Linux CI (GameCI containers share a hardcoded `/etc/machine-id`, so Unity sees them as one machine). Windows builds must share the remaining seat, which means all of CI (Linux + Windows) shares 1 seat. Windows builds must run after Linux builds finish, not just after each other. Concurrent workflows (push to main + dev simultaneously) also need coordination — a GitHub `concurrency` group would queue Windows activation across workflows.

If a runner crashes mid-build, the license isn't returned (recoverable via Unity ID portal, but manual).

### Approaches evaluated

| Approach | Install overhead | Licensing | Cost | Risk |
|---|---|---|---|---|
| **Serialize + native install** | 10-20 min cold, 3-8 min cached (5-7 GB eats most of 10 GB cache budget) | Serialize all Windows after Linux + concurrency group across workflows | $0 | Low — slow but reliable |
| **Windows Docker + VS mount** | None (Unity in image) | Custom image could hardcode identity (partial — registry yes, SMBIOS no) | $0 | High — VS mount fragile, DNS/IPC issues reported |
| **Self-hosted runner** | None (permanent install) | 1 consistent seat | $0 + hardware | Medium — maintenance burden |
| **Managed runners (Buildalon)** | None (persistent VMs) | Handled | $40-180/mo | Medium — single-person project, governance risk |
| **GitHub custom images** | None (baked in) | Depends on approach | Requires Team/Enterprise plan | Low-Medium |
| **Skip win64 CI** | N/A | N/A | $0 | Accept the gap |

### Untested assumption: shared HardwareId on `windows-latest`

If GitHub's hosted Windows runners share the same machine identity signals that Unity licensing checks (likely the Windows Product ID), then native-runner activation would consume only 1 seat — the same trick that works on Linux, but via Azure's VM provisioning rather than a hardcoded container ID. This would make serialization simpler (no cross-workflow seat conflicts, parallel Windows builds safe). A test workflow dumping WMI values across parallel jobs would confirm or rule this out. See licensing research doc section 5 for the proposed test.

## Design decisions

1. **Two separate jobs** (not conditional matrix). The `build-linux` job uses GameCI Linux containers; `build-windows` uses `windows-latest` runners. Clean separation, no conditional YAML.
2. ~~**GameCI `windows-il2cpp` containers**~~ — Withdrawn. GameCI Windows Docker containers require mounting VS Build Tools from the host (fragile path coupling), don't hardcode machine-id (licensing issues), and have known DNS/IPC bugs. Not viable.

## Next step

**Decision needed:** choose a Windows IL2CPP CI strategy. Options: serialize + native install (slow, free, reliable), self-hosted runner (free, fast, maintenance burden), skip win64 CI (accept the gap), or paid managed runners ($40/mo). Before deciding, consider running a test workflow that dumps `windows-latest` machine identity values across parallel jobs — the result determines whether native-runner builds can share a single license seat, which narrows the licensing side of the trade-off (though not the install-time problem).

## Done when

- win64 matrix entries build successfully with IL2CPP scripting backend
- Windows builds run on a Windows environment (runner or container)
- All other builds remain unchanged on Linux/GameCI
