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

## Root cause (identified)

The cache key in `unity.yml` is **per-project but not per-platform**:

```yaml
key: unity-library-${{ matrix.project-name }}-${{ hashFiles(...) }}
```

All three Outernet.Client builds (linux64, android-mobile, magicleap) share **one cache entry**. Whichever platform finishes first on a cold run saves its Library — in practice, android-mobile wins the race. The linux64 and magicleap builds then restore an android-flavored Library that contains platform-specific artifacts (Bee build graph, shader cache, player data cache) for the wrong platform.

CI logs confirm this. Most recent run (2026-03-04):

| Build | Cache status | Shader cache hits | Build time |
|---|---|---|---|
| Outernet.Client (android) | HIT (exact key) | All local hits | 8m 41s |
| Outernet.Client (magicleap) | HIT (exact key) | 0 local hits | 34m 29s |
| Outernet.Client (linux64) | HIT (exact key) | 0 local hits | 58m 40s |
| AndroidMobile (android) | HIT (exact key) | All local hits | 7m 23s |
| MapRegistrationTool (linux64) | HIT (exact key) | All local hits | 6m 24s |

The fix is to add `${{ matrix.platform }}` to the cache key. But this creates a cache budget problem.

## Cache budget constraint

GitHub Actions cache has a **10 GB per-repo limit** (free tier). Current usage:

| Cache | Size |
|---|---|
| unity-library-Outernet.Client | 3.71 GiB |
| unity-library-AndroidMobile | 2.84 GiB |
| unity-library-MapRegistrationTool | 2.29 GiB |
| Total | ~8.84 GiB |

With per-platform keys, Outernet.Client would need 3 separate caches (~3.7 GiB each), pushing total to ~16 GiB — well over the 10 GiB limit. LRU eviction would kick in, causing periodic cold-cache builds (unacceptable).

As of Nov 2025, GitHub allows exceeding 10 GB with a paid plan (Pro/Team/Enterprise). Pricing is ~$0.07/GB/month. The project is FOSS/non-profit and wants to avoid paying.

## Areas to investigate (revised)

The original list was mostly wrong — `Library/Bee/`, shader cache, etc. are all inside `Library/` and already cached. The real issues are:

1. **Per-platform cache keys** — the primary fix. Requires solving the budget problem.
2. **Trimming cached content** — exclude `Library/PackageCache/` (~1.6 GiB per project, re-downloaded from UPM registry on each run in ~1-2 min) to free budget for per-platform keys. Estimated total with trimming: ~8.2 GiB (fits in 10 GiB, but tight).
3. **Machine-level Bee cache** (`BEE_CACHE_DIRECTORY` at `~/.cache/unity3d/bee`) — separate from `Library/Bee/`. Currently not cached in CI. Unclear whether it provides value beyond what `Library/Bee/` already provides when the project-local cache is warm. Needs empirical testing.
4. **Minor Docker CI gaps** — no Go module cache mount in `database-migrator` Dockerfile, no NuGet cache mount in `state-sync` Dockerfile. Small impact but easy wins.

## Research: Unity Library internals

The Library directory for MapRegistrationTool (4.8 GiB total):

| Directory | Size | Content-addressed? | Platform-specific? |
|---|---|---|---|
| `Bee/` | 2.9 GiB | Partially (CachedNodeOutput is MD5-keyed) | Yes — build artifacts are platform-specific |
| `PackageCache/` | 1.6 GiB | No (name@registry-hash) | No — packages are platform-independent |
| `Artifacts/` | 126 MB | Yes (hash-bucketed `00/`-`ff/`) | Yes — platform is part of the hash |
| `BurstCache/` | 144 MB | No | Yes |
| `ShaderCache/` | 36 MB | No (name-based directories) | Yes |
| `ScriptAssemblies/` | 34 MB | No | Partially |

Unity has two built-in cross-project deduplication mechanisms:
- **`BEE_CACHE_DIRECTORY`** (`~/.cache/unity3d/bee`) — machine-wide Bee cache for reusable build components (libIL2CPP, non-embedded package compilations)
- **Global UPM cache** (`~/.cache/Unity/upm/`) — shared package tarballs, configurable via `UPM_CACHE_PATH`

Unity Accelerator (network-level import cache) exists but is **proprietary** — violates FOSS-only principle.

## Research: Docker CI caching (already good)

The Docker build pipeline is well-optimized:
- Registry-based layer cache (`mode=max`) to `ghcr.io/.../build-cache` — no size limit
- BuildKit `--mount=type=cache,id=uvcache` — all Dockerfiles share one uv download cache
- Lock-file-before-source pattern in every Dockerfile
- `setup-uv` with `enable-cache: true` for host-side uv cache

## Key files

- `.github/workflows/unity.yml` — cache configuration (the main target)
- `scripts/src/scripts/build_unity.py` — build output paths

## Done when

- Root causes of slow warm-cache builds identified (**done** — cross-platform cache sharing)
- At least one optimization implemented that measurably reduces the slowest build time

## Next step

**Empirical test: machine-level Bee cache behavior — must run in CI, not locally.** The COI container has Unity installed but no license (CI uses `UNITY_SERIAL`/`UNITY_EMAIL`/`UNITY_PASSWORD` secrets for activation). Local builds fail with "No valid Unity Editor license found."

Approach: add diagnostic steps to the Unity CI workflow (on a branch) that capture cache state before and after builds:

1. Add a step after the build that runs `du -sh ~/.cache/unity3d/bee` and `ls -la ~/.cache/unity3d/bee/` to see if/what the machine-level Bee cache contains after a build
2. Add a step that runs `du -sh ${{ matrix.project }}/Library/Bee/` to measure per-platform Library/Bee size
3. Run this on a push to observe the results

If `~/.cache/unity3d/bee` is populated and non-trivial, a follow-up experiment would cache it and measure whether it speeds up builds.

Independently, the primary fix (add `${{ matrix.platform }}` to cache key) can proceed in parallel with the "trim `Library/PackageCache/`" strategy to fit within 10 GiB. Estimated sizes without PackageCache: ~8.2 GiB total (tight but feasible). This should be tested by pushing the change and measuring actual cache sizes from CI logs.
