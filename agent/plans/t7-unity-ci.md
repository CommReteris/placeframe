# T7: Unity client builds with GameCI

See `ci-background.md` for shared CI context.

## Goal

Automated Unity builds for the XR client application in CI.

## Context

Placeframe includes a Unity client (ARFoundation-based XR app) that needs to be built for target platforms. GameCI is the standard open-source solution for Unity CI on GitHub Actions.

## Key considerations

- **License activation**: Personal licenses expire periodically and require manual `.ulf` regeneration. Professional licenses use a serial key and are more reliable. Budget for a Pro license if CI matters.
- **Disk space**: Unity Docker images are multi-GB, and the Library cache can be 1-10+ GB. The `free-disk-space` action is already used in `build.yml` and will be needed here too.
- **IL2CPP**: If targeting iOS/Android with IL2CPP, builds must run on the matching OS (Linux IL2CPP → Linux targets only, Windows IL2CPP → Windows targets only). macOS requires a macOS runner (no Docker).
- **Library caching**: Cache the `Library/` folder keyed on `Assets/**`, `Packages/**`, `ProjectSettings/**` hashes. This can cut build times by 50%+.
- **Separate workflow**: `.github/workflows/unity.yml` with path-based triggers on the Unity project directory. Independent from Docker builds.
- **Generated API client**: The C# API client in `packages/generated/csharp/` is consumed by Unity. If the client generation workflow and Unity build are separate, need artifact passing or a "generate then build" workflow chain.

**GameCI v3 roadmap** aims for a CI-agnostic CLI, which would help with the GitHub Actions vendor risk concern. Worth monitoring but not ready yet.

## Depends on

Nothing. T4 informs trigger strategy but doesn't block.

## Done when

**Verifiable now (no special infra):**
- Workflow file `.github/workflows/unity.yml` exists
- `act --list` parses it

**Requires hardware/infra (verify manually later):**
- Unity build completes on GitHub Actions
