---
id: T64
title: Investigate layer caching for COI image rebuilds
status: design-needed
depends_on: []
---

# T64: Investigate layer caching for COI image rebuilds

## Goal

Make iterating on `agent/coi-placeframe-build.sh` less painful by avoiding full re-execution of the build script on every `--rebuild`. Currently a rebuild re-downloads ~15-20 GB of Unity editor + modules even when only a late-stage command changed.

## Context

`coi build custom` launches a container from the base `coi` image, runs the entire build script, then publishes the result. There is no Docker-style layer caching — every `--rebuild` starts from scratch. T62 required three rebuild cycles to land (two bugs caught sequentially), each taking 20+ minutes for the Unity download alone.

Possible approaches:
- **Intermediate images**: split the build into stages (e.g. `coi-placeframe-base` with system deps + Unity, then `coi-placeframe` adding project-specific tooling on top). Rebuild only the top layer when late-stage commands change.
- **Incus snapshots**: take snapshots at checkpoints during the build, restore from the latest valid snapshot on rebuild.
- **Script-level idempotency**: make each section of the build script detect whether its work is already done and skip accordingly (unityhub already installed? skip. Editor already in /opt/unity? skip install).
- **Test in running container first**: establish a workflow convention where new build commands are tested interactively in a running container before baking into the image (this is what we did for T62's third bug).

## Key files

- `agent/coi-placeframe-build.sh` — the build script that would be split or made idempotent
- `scripts/src/scripts/setup_agent_sandbox.py` — orchestrates image creation, would need to support multi-stage builds

## Approach

Design needed — evaluate which approach (or combination) gives the best iteration speed vs. complexity tradeoff.

## Done when

- Rebuilding after a change to a late-stage build command does not re-download Unity
- The approach is documented so future build script changes follow the pattern
