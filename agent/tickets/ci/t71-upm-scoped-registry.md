---
id: T71
title: Set up scoped UPM registry for Placeframe Unity packages
status: design-needed
depends_on: []
---

# T71: Set up scoped UPM registry for Placeframe Unity packages

## Goal

Host Placeframe UPM packages (and the Cesium Linux fork from T69/T70) on a scoped registry so Unity projects can resolve them like any other package dependency.

## Context

The Placeframe Unity projects consume custom packages (e.g. `com.placeframe.zed-client`). A scoped registry would provide a proper distribution channel instead of local file paths or git URLs. T70 (Cesium native CI) depends on this for publishing the Linux-augmented Cesium package.

## Done when

- [ ] Scoped registry running and accessible from dev machines and CI
- [ ] At least one Placeframe package published and resolvable
- [ ] Unity project manifests updated to use the registry
