---
id: T78
title: Investigate and reduce Unity CI build times
status: design-needed
depends_on: [T7]
---

# T78: Investigate and reduce Unity CI build times

## Goal

Reduce wall-clock time for Unity CI builds. Current warm-cache times range from ~8 min (smaller projects) to 27+ min (Outernet.Client linux64/magicleap). Identify bottlenecks and optimize.

## Context

T7 established the Unity CI workflow with Library caching. First-run (cold cache) results:

| Build | Cold | Warm |
|---|---|---|
| AndroidMobile (android) | 31m42s | 7m48s |
| Outernet.Client (android) | 39m42s | 9m35s |
| MapRegistrationTool (linux64) | 45m2s | 8m27s |
| Outernet.Client (magicleap) | 41m7s | ~27m+ |
| Outernet.Client (linux64) | 50m+ | ~27m+ |

Caching cut smaller builds by 4-5x. The two large Outernet.Client builds still take a long time even with warm caches — likely dominated by IL2CPP C++ compilation (linux64) and shader compilation (magicleap).

## Areas to investigate

- IL2CPP incremental build cache effectiveness — is `Library/Bee/` actually being reused across runs?
- Bee machine-level cache (`BEE_CACHE_DIRECTORY`) — caching `~/.cache/unity3d/bee` separately
- Shader compilation cache
- Build output directory persistence for C++-level incremental compilation
- NuGet restore caching (currently restores every run)
- Whether `actions/cache` size limits are truncating the Library cache for large projects

## Key files

- `.github/workflows/unity.yml` — cache configuration
- `scripts/src/scripts/build_unity.py` — build output paths

## Done when

- Root causes of slow warm-cache builds identified
- At least one optimization implemented that measurably reduces the slowest build time
