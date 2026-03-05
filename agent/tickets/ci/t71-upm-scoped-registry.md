---
id: T71
title: Set up scoped UPM registry for Placeframe Unity packages
status: blocked
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

- [x] Package.json metadata correct (license, repository, inter-package deps)
- [x] Publish workflow created (`.github/workflows/publish-upm.yml`)
- [x] Manifest.json files updated with scoped registry entries and version refs
- [ ] `NPM_TOKEN` secret added to GitHub repo
- [ ] Publish workflow triggered and all 3 packages live on npmjs.org (`npm view com.placeframe.vps` returns metadata)
- [ ] UnityNuGet packages (`org.nuget.placeframeapiclient`, `org.nuget.placeframezedclient`) verified resolvable from Unity
- [ ] At least one Unity project opens and resolves all packages from registries (no `file:` path fallback)

## Design decisions

- **npmjs.org as the registry.** GitHub Packages was considered but forces `@scope/` naming that's unproven with Unity UPM. npmjs.org supports unscoped `com.placeframe.*` names, is already used by the project (Magic Leap packages), and the rug-pull risk is negligible (too foundational to the npm ecosystem). No need for self-hosted Verdaccio.
- **Generated clients via UnityNuGet, not npm.** PlaceframeApiClient and PlaceframeZedClient are already published to NuGet (v0.1.3) and served as UPM packages via the UnityNuGet registry at `https://unitynuget-registry.openupm.com` with `org.nuget.*` names.
- **Proper dependency resolution is the primary driver.** With `file:` paths, transitive dependencies don't resolve — consumers must manually list everything. A registry lets the package manager handle the dependency tree.

## Branch

`t71-upm-registry` (based on `ci-stuff`)

## Log

- Manifests were updated to point at registry versions (`"1.0.0"`) but the packages were never published to npmjs.org — all 3 return 404. The publish workflow has never been run because it only exists on the feature branch (not the default branch), and no `NPM_TOKEN` secret has been configured.
- All Unity projects are currently broken on this branch: manifests reference unpublished registry versions instead of `file:` paths.

## Observations

- `apps/MakeItSing/Packages/manifest.json` had hardcoded Windows absolute paths (`file:C:/Users/epjec/Documents/Plerion/...`) for Placeframe packages. Fixed by switching to registry references. Other `file:` paths in this project (fofx packages) still use relative paths correctly.

## Blocked on

- **npm credentials**: need an npm account with a granular access token scoped to `com.placeframe.*`, added as `NPM_TOKEN` repo secret in GitHub
- **Workflow on default branch**: `publish-upm.yml` must be on `main` before GitHub Actions can discover it for `workflow_dispatch`
- **Unity verification**: need a machine with Unity to confirm packages resolve from registries after first publish

## Next step

User: create npm token, add `NPM_TOKEN` secret, merge workflow to `main`, trigger first publish. Then open a Unity project and verify resolution.
