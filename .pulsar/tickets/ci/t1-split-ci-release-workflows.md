---
id: T1
title: Replace versions.json with per-package git tags
status: plan-needed
depends_on: []
---

# T1: Replace versions.json with per-package git tags

## Goal

Eliminate `versions.json` as the version source of truth for packages and releases. Replace it with per-package git tags (`core-v1.0.3`, `api-client-v0.1.5`, `release-v0.2.0`). This removes one of the two sources of main-only commits that prevent fast-forward merges from dev→main (prerequisite for T3).

## Context

Currently `versions.json` serves three roles:
1. **Version tracking** — stores the current version number for each package, app, and the release counter
2. **Change detection** — stores content hashes per package; `publish_packages.py` compares current hash to stored hash to decide whether to publish
3. **State mutation** — both `publish_packages.py` (updates package versions + hashes) and `create_release.py` (bumps release version) write to this file, and `commit_artifacts.py` commits it to the current branch

The problem: these commits happen on main during release, creating main-only commits that prevent dev→main fast-forward merges. Git tags can replace all three roles:
- **Version tracking**: tag name encodes the version (`core-v1.0.3`)
- **Change detection**: `git diff --quiet <last-tag> -- <package-path>` replaces hash comparison
- **State mutation**: creating a tag is not a commit — no branch divergence

The `package.json` files in `packages/unity/Placeframe/Assets/Package/*/` are also committed by `commit_artifacts.py` after `publish_packages.py` patches their version fields for npm publish. But these version fields are unused by Unity's `file:` resolution (confirmed by comment at `publish_packages.py:67-72`). Setting them to `0.0.0-local` permanently and patching ephemerally during publish eliminates this commit source too.

### Tag naming convention

| Artifact | Tag pattern | Example |
|---|---|---|
| Release counter | `release-v{major}.{minor}.{patch}` | `release-v0.2.0` |
| API client (NuGet) | `api-client-v{major}.{minor}.{patch}` | `api-client-v0.1.5` |
| Core (npm) | `core-v{major}.{minor}.{patch}` | `core-v1.0.3` |
| ARFoundation (npm) | `arfoundation-v{major}.{minor}.{patch}` | `arfoundation-v1.0.3` |
| MagicLeap (npm) | `magicleap-v{major}.{minor}.{patch}` | `magicleap-v1.0.3` |

App versions (`Outernet.Client`, `MapRegistrationTool`, `AndroidMobile`) are also tracked in `versions.json`. These need tags too, or an alternative — `publish_packages.py` computes app hashes and bumps their versions in the "Compute app versions" step.

### Change detection: hash comparison vs git diff

Current approach (`publish_packages.py`):
```python
hasher = hashlib.sha256()
for file in sorted(config.path.rglob(config.hash_glob)):
    hasher.update(str(file.relative_to(config.path)).encode())
    hasher.update(file.read_bytes())
changed = hashes[name] != old_hash
```

Proposed approach:
```python
last_tag = get_latest_tag(f"{name}-v*")
changed = not git_diff_quiet(last_tag, "HEAD", "--", str(config.path))
```

The git diff approach is simpler and doesn't require storing hashes. It also correctly handles file deletions and renames, which the hash approach handles but less intuitively.

Edge case: on first run (no tags exist), everything should be considered changed and published. The scripts must handle the "no matching tag" case gracefully.

### Dependency cascading

`publish_packages.py` has a `depends_on` mechanism: if `core` is published, `arfoundation` and `magicleap` are also published (they depend on `core`). The git diff approach must preserve this — if the diff says `core` changed, dependents must also be published even if their own paths haven't changed. This is already handled in the current code and just needs to be preserved.

## Key files

**Modify:**
- `build/src/build_scripts/placeframe/ci/publish_packages.py` — replace `STATE_FILE` reads/writes with git tag queries and creation; use `git diff` for change detection; remove hash computation; patch `package.json` ephemerally without committing
- `build/src/build_scripts/placeframe/ci/create_release.py` — read release version from `release-v*` tags; bump and create new tag; remove `versions.json` write and commit
- `build/src/build_scripts/placeframe/ci/commit_artifacts.py` — remove `versions.json` and `package.json` from `git add` line (only `.env.lock` remains; may be deleted entirely in T2)

**Delete:**
- `build/versions.json`

**Set to `0.0.0-local`:**
- `packages/unity/Placeframe/Assets/Package/Core/package.json`
- `packages/unity/Placeframe/Assets/Package/ARFoundation/package.json`
- `packages/unity/Placeframe/Assets/Package/MagicLeap/package.json`

**Workflow (minor update):**
- `.github/workflows/placeframe.yml` — remove `build/versions.json` from `paths-ignore` list; remove the `publish` job's "Upload publish artifacts" step (no more `versions.json` artifact); remove `commit` job's "Download publish artifacts" step

## Approach

1. Create initial git tags matching current `versions.json` values (one-time bootstrap)
2. Refactor `publish_packages.py`: replace hash-based change detection with `git diff --quiet <last-tag>`, replace `STATE_FILE` reads with `git tag --list` + version parsing, create per-package tags after successful publish, remove `STATE_FILE` write
3. Refactor `create_release.py`: replace `STATE_FILE` read with `git tag --list "release-v*"` + semver sort, create `release-v{new}` tag, remove `STATE_FILE` write and git commit
4. Update `commit_artifacts.py`: remove `versions.json` and `package.json` from git add
5. Set `package.json` versions to `0.0.0-local`
6. Delete `versions.json`
7. Update workflow `paths-ignore` and remove publish artifact upload/download steps

## Done when

**Verifiable now:**
- [ ] `build/versions.json` is deleted from the repo
- [ ] Git tags exist for all current package and release versions
- [ ] `package.json` version fields are `0.0.0-local`
- [ ] `publish_packages.py` reads versions from git tags, uses `git diff` for change detection, creates per-package tags on publish
- [ ] `publish_packages.py` handles "no tag exists" case (first publish)
- [ ] `publish_packages.py` preserves dependency cascading (`depends_on`)
- [ ] `create_release.py` reads version from `release-v*` tags, creates tag without committing
- [ ] `commit_artifacts.py` no longer stages `versions.json` or `package.json`
- [ ] Workflow no longer uploads/downloads `versions` artifact

**Requires manual verification:**
- [ ] Publishing a changed package creates the correct tag
- [ ] Publishing with no changes is a no-op
- [ ] Dependency cascade works (changing core triggers arfoundation + magicleap publish)
- [ ] Release creates correct `release-v{N}` tag

## Next step

Enter plan mode to detail the git tag query logic — particularly: how to find the latest tag matching a pattern (semver sort vs `git tag --sort=-v:refname`), how to handle the bootstrap case, and whether app versions need tags or a different approach.
