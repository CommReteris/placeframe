---
id: T75
title: "Win64 CI: switch from Linux cross-compilation to dedicated Windows runners"
status: design-needed
depends_on: [T7]
---

# T75: Win64 CI: switch from Linux cross-compilation to dedicated Windows runners

## Goal

Replace the Linux cross-compilation approach for win64 Unity builds with dedicated Windows runners (`windows-latest`) using a native Unity installation and IL2CPP scripting backend.

## Context

T7 implements the Unity CI workflow with all 7 builds running on Linux using GameCI containers. The two win64 builds (Outernet.Client, MapRegistrationTool) were originally configured with the `windows-mono` module for cross-compilation, but this fails because the projects use IL2CPP as their scripting backend. Win64 matrix entries are commented out in `unity.yml` until this ticket is resolved. Switching to Windows runners enables IL2CPP builds and native toolchain access (Visual Studio, Windows SDK).

## Key files

- `.github/workflows/unity.yml` — split win64 matrix entries to use `windows-latest`
- `scripts/src/scripts/build_unity.py` — may need path adjustments for Windows Unity install location

## Research

See `agent/research/unity-ci-licensing.md` for full analysis of Unity licensing in CI.

**Key finding:** GameCI Linux containers all share a hardcoded `machine-id`, so Unity sees 5 parallel builds as one machine (1 activation slot). GameCI Windows containers do NOT have this — each gets a unique machine hash, consuming a separate slot. With a 2-seat serial limit, parallel Windows builds will exceed the cap.

**First action on pickup: choose a licensing strategy for Windows builds.** Options ranked by cost:

1. **Serialize Windows builds** — run win64 sequentially, activate/return before next ($0, adds wall-clock time)
2. **Second Personal license** — separate Unity account for Windows CI ($0, parallel)
3. **Native runner activation** — install Unity directly on `windows-latest` without Docker; may share GitHub's HardwareId ($0, untested)
4. **Unity Pro + Build Server** — officially supported floating licenses ($2,640/year)

## Design decisions

1. **Two separate jobs** (not conditional matrix). The `build-linux` job uses GameCI Linux containers; `build-windows` uses `windows-latest` runners. Clean separation, no conditional YAML.
2. **GameCI `windows-il2cpp` containers** (same architecture as Linux). Not a native Unity install. Keeps both platforms using the GameCI container approach. Contingent on licensing strategy — if we can't run parallel Windows containers, may need to serialize or use native runner install instead.

## Done when

- win64 matrix entries run on `windows-latest` with native Unity installation
- Unity installation is cached to avoid re-downloading 4.5GB per run
- IL2CPP scripting backend is used for Windows standalone builds
- All other builds remain unchanged on Linux/GameCI
