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

T7 implements the Unity CI workflow with all 7 builds running on Linux using GameCI containers. The two win64 builds (Outernet.Client, MapRegistrationTool) use the `windows-mono` module for cross-compilation, which restricts them to the Mono scripting backend. Switching to Windows runners enables IL2CPP builds and native toolchain access (Visual Studio, Windows SDK).

## Key files

- `.github/workflows/unity.yml` — split win64 matrix entries to use `windows-latest`
- `scripts/src/scripts/build_unity.py` — may need path adjustments for Windows Unity install location

## Done when

- win64 matrix entries run on `windows-latest` with native Unity installation
- Unity installation is cached to avoid re-downloading 4.5GB per run
- IL2CPP scripting backend is used for Windows standalone builds
- All other builds remain unchanged on Linux/GameCI
