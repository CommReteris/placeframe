---
id: T87
title: Content-hash versioning for UPM packages
status: design-needed
depends_on: [T86]
---

# T87: Content-hash versioning for UPM packages

## Goal

Add content-hash-triggered version bumping to the three `org.outernet.placeframe*` UPM packages in `publish-upm.yml`, so CI auto-bumps and publishes when package source changes. Currently the version in each `package.json` must be bumped manually — if someone changes the package source but forgets to bump the version, the `npm view` idempotency check silently skips publishing and the registry stays stale.

## Context

Same failure mode as T86 (NuGet API client went stale because nobody bumped the version). The UPM packages haven't been bitten yet, but the risk is identical: human forgets to bump version → CI skips → consumers get stale package.

T86 will implement content-hash-triggered versioning for the NuGet API client first. This ticket applies the same pattern to the three UPM packages published by `publish-upm.yml`:

- `org.outernet.placeframe` (Core)
- `org.outernet.placeframe.arfoundation` (ARFoundation)
- `org.outernet.placeframe.magicleap` (MagicLeap)

## Key files

- `.github/workflows/publish-upm.yml` — existing UPM publish workflow
- `packages/unity/Placeframe/Assets/Package/Core/package.json`
- `packages/unity/Placeframe/Assets/Package/ARFoundation/package.json`
- `packages/unity/Placeframe/Assets/Package/MagicLeap/package.json`

## Open questions

- Should the hash-and-bump mechanism be shared with T86 (reusable action or script), or kept independent?
- What constitutes "package source" for hashing? Just `.cs` files, or also `.asmdef`, `package.json` (minus version field), resources?

## Done when

- [ ] CI auto-bumps patch version and publishes when package content changes
- [ ] No publish occurs when content is unchanged
- [ ] Version bump strategy documented
