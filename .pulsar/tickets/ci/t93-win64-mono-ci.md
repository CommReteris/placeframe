---
id: T93
title: "Win64 CI: enable Mono builds (cross-compiled from Linux)"
status: ready
depends_on: [T7]
---

# T93: Win64 CI: enable Mono builds (cross-compiled from Linux)

## Goal

Uncomment the two win64 matrix entries in `build-unity.yml` to get Windows build coverage in CI using the Mono scripting backend cross-compiled from Linux.

## Context

T75 tracks the full win64 IL2CPP CI story (self-hosted Windows runner, VS Build Tools, etc.). That work is blocked on hardware access. In the meantime, the Mono scripting backend can be cross-compiled from Linux using GameCI's `windows-mono` container image — no Windows runner or MSVC needed.

The workflow matrix already has the two win64 entries commented out with `module: windows-mono`, and `build_unity.py` already handles `--platform win64` with `-buildWindows64Player`. This is a configuration-only change.

Mono builds don't match the production IL2CPP backend, so they won't catch IL2CPP-specific issues (AOT compilation failures, stripping problems). But they do catch C# compilation errors, missing references, and platform-specific `#if` guard issues on Windows — which is the majority of what CI is for.

## Key files

- `.github/workflows/build-unity.yml:51-56,62-64` — commented-out win64 matrix entries to uncomment

## Approach

Uncomment the two win64 matrix entries. No other changes needed — the build script, caching, and artifact collection all handle win64 already.

## Done when

- Outernet.Client (win64) and MapRegistrationTool (win64) build successfully in CI using the `windows-mono` GameCI image
- All existing builds remain unaffected
