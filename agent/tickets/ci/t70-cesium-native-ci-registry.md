---
id: T70
title: Automate Cesium native Linux build and publish to UPM registry
status: blocked
depends_on: [T69]
---

# T70: Automate Cesium native Linux build and publish to UPM registry

## Goal

Move the manual Cesium native Linux build (T69) into CI and publish the resulting package to the scoped UPM registry. Remove the committed binary from the repo.

## Context

T69 commits a manually-built forked `com.cesium.unity` package with Linux binaries directly to the repo as a temporary measure. This ticket replaces that with an automated build that publishes to the same scoped registry being set up for Placeframe UPM packages.

## Done when

- [ ] CI job builds CesiumForUnityNative for Linux from source
- [ ] Built package published to scoped UPM registry
- [ ] Outernet.Client manifest points at registry instead of local file path
- [ ] Committed binary removed from repo
- [ ] Rebuild triggers documented (manual or on Cesium version bump)
