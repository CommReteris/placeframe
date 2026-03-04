---
id: T71
title: Set up scoped UPM registry for Placeframe Unity packages
status: in-review
depends_on: []
branch: t71-upm-registry
plan: t71-plan.md
---

# T71: Set up scoped UPM registry for Placeframe Unity packages

## Goal

Host Placeframe UPM packages on a scoped registry so Unity projects can resolve them like any other package dependency, with proper transitive dependency resolution.

## Context

The Placeframe Unity projects consume custom packages (`com.placeframe.vps`, `com.placeframe.vps.arfoundation`, `com.placeframe.vps.magicleap`, plus generated clients). All are currently referenced via `file:` relative paths in each project's `Packages/manifest.json`. This means consuming projects must manually list every transitive dependency — the package manager can't resolve the dependency tree automatically. A proper registry fixes this.

Current packages:
- `com.placeframe.vps` (core) — used by all projects
- `com.placeframe.vps.arfoundation` — AR Foundation camera support
- `com.placeframe.vps.magicleap` — Magic Leap camera support
- `com.placeframe.api-client` — generated API client (on NuGet as PlaceframeApiClient)
- `com.placeframe.zed-client` — generated ZED client (on NuGet as PlaceframeZedClient)
- `com.cesium.unity` (Linux fork) — used by MapRegistrationTool, MakeItSing

Projects already configure scoped registries for Magic Leap (npmjs.org) and Cesium (unity.pkg.cesium.com), so the pattern is established.

## Key files

- `packages/unity/Placeframe/Assets/Package/*/package.json` — UPM package definitions
- `apps/*/Packages/manifest.json` — consumer project manifests (add scoped registry, switch from file: to version refs)
- `legacy/Outernet.Client/Packages/manifest.json` — same
- `.github/workflows/publish-upm.yml` — publish workflow (new)

## Approach

Publish `com.placeframe.vps*` packages to npmjs.org (the public npm registry). Generated C# clients are already on NuGet and available via the UnityNuGet registry (`https://unitynuget-registry.openupm.com`). Fix package.json metadata (license, repository, missing inter-package deps), create a CI publish workflow, and update all manifest.json files to use registry references instead of `file:` paths. See `agent/plans/t71-plan.md` for full details.

## Done when

- [ ] Scoped registry running and accessible from dev machines and CI
- [ ] At least one Placeframe package published and resolvable
- [ ] Unity project manifests updated to use the registry

## Design decisions

- **npmjs.org as the registry.** GitHub Packages was considered but forces `@scope/` naming that's unproven with Unity UPM. npmjs.org supports unscoped `com.placeframe.*` names, is already used by the project (Magic Leap packages), and the rug-pull risk is negligible (too foundational to the npm ecosystem). No need for self-hosted Verdaccio.
- **Generated clients via UnityNuGet, not npm.** PlaceframeApiClient and PlaceframeZedClient are already published to NuGet (v0.1.3) and served as UPM packages via the UnityNuGet registry at `https://unitynuget-registry.openupm.com` with `org.nuget.*` names.
- **Proper dependency resolution is the primary driver.** With `file:` paths, transitive dependencies don't resolve — consumers must manually list everything. A registry lets the package manager handle the dependency tree.

## Branch

`t71-upm-registry` (based on `ci-stuff`)

## Log

Clean implementation, no issues.

## Observations

- `apps/MakeItSing/Packages/manifest.json` had hardcoded Windows absolute paths (`file:C:/Users/epjec/Documents/Plerion/...`) for Placeframe packages. Fixed by switching to registry references. Other `file:` paths in this project (fofx packages) still use relative paths correctly.

## Requires manual verification

- Add `NPM_TOKEN` repository secret in GitHub (npm granular access token)
- Trigger `publish-upm.yml` via workflow_dispatch to publish packages to npmjs.org
- Verify `npm view com.placeframe.vps` returns package metadata
- Open each Unity project and confirm all packages resolve from registries (vps packages won't resolve until first publish)
- Note: Unity CI builds will fail until the first npm publish completes, since manifest.json now references registry versions instead of `file:` paths
