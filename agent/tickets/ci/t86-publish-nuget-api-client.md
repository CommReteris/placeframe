---
id: T86
title: Automate NuGet API client publish to npm registry
status: design-needed
depends_on: [T71]
---

# T86: Automate NuGet API client publish to npm registry

## Goal

Publish the generated C# API client (`org.nuget.placeframeapiclient`) to npmjs.org automatically so Unity projects always resolve a version that matches the current API schema. Currently published manually — version `0.1.3` on npm is stale and missing fields that the placeframe Unity package already references (`NumInliers`, `InlierCoverage`, `NumCorrespondences`, `NumMatches` on `LocalizationMetrics`).

## Context

The C# API client is generated from the API's OpenAPI spec via `uv run generate-clients`. The generated source lives at `packages/generated/csharp/api-client/src/PlaceframeApiClient/`. Unity projects consume it as `org.nuget.placeframeapiclient` from the `org.nuget` scoped registry on npmjs.org.

The source is up to date (has all 6 `LocalizationMetrics` fields), but the published npm package (`0.1.3`) was manually published before these fields were added. This causes Unity compilation failures in MapRegistrationTool and AndroidMobile.

## Key files

- `packages/generated/csharp/api-client/src/PlaceframeApiClient/` — generated C# source
- `.github/workflows/publish-upm.yml` — existing UPM publish workflow (candidate for adding this step)
- `apps/MapRegistrationTool/Packages/manifest.json` — consumer (references `org.nuget.placeframeapiclient`)
- `legacy/Outernet.Client/Packages/manifest.json` — consumer

## Open questions

- Should this be a step in `publish-upm.yml` or a separate workflow? The API client is generated (not a UPM package per se), but it follows the same publish pattern.
- How to package a .NET library as an npm package for Unity's NuGet-via-npm consumption? Need to understand what `org.nuget.placeframeapiclient@0.1.3` contains (DLL? source? NuGet `.nupkg` repackaged as npm `.tgz`?). The packaging format determines the CI steps.
- Version bumping strategy — should the version track the API spec (e.g. hash-based) or use manual semver?

## Done when

- [ ] CI publishes `org.nuget.placeframeapiclient` to npmjs.org after API client regeneration
- [ ] Published package includes all current `LocalizationMetrics` fields
- [ ] Unity projects compile without `LocalizationMetrics` errors
- [ ] Version bump strategy documented
