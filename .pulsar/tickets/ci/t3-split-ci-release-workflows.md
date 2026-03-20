---
id: T3
title: Split CI and release into separate workflows
status: plan-needed
depends_on: [T1, T2]
---

# T3: Split CI and release into separate workflows

## Goal

Split the single `placeframe.yml` workflow into `ci.yml` (builds on dev) and `release.yml` (releases on main). Since T1 and T2 eliminate all commits during release, main is always a fast-forward of dev, so the commit SHA is identical on both branches. The release workflow reuses CI artifacts by looking up the successful CI run for the same SHA via the GitHub REST API.

## Context

After T1 (tag-based versioning) and T2 (SHA-based image refs), no workflow job creates commits on any branch. This means:
- The dev→main merge via the release gate PR is a true fast-forward
- The commit SHA on main after merge is identical to the SHA on dev where CI ran
- CI artifacts (Unity builds) uploaded on the dev run can be downloaded by the release workflow on main using the same SHA

### Current workflow structure (`placeframe.yml`)

```
push: [main] + pull_request: [main, dev] + workflow_dispatch

preflight ──────────────────────┐
activate-license ───────────────┤
matrix ─────────────────────────┤
build-docker (3 variants) ──────┤
build-unity (matrix) ───────────┤
publish (main only) ────────────┤
commit (main + PR branches) ────┤
release (main only) ────────────┘
```

Problems with this structure:
- `push: [main]` re-runs the entire pipeline after fast-forward merge, wasting CI minutes
- `publish`, `commit`, and `release` only run on main but share a workflow with CI jobs
- `commit` runs on PR branches too, pushing bot commits unnecessarily
- `ensure-release-pr` is a separate workflow (`placeframe-release-pr.yml`) that fires on every dev push regardless of CI status

### Proposed structure

**`ci.yml`** — triggered on `push: [dev]`, `pull_request: [main, dev]`, `workflow_dispatch`:
```
preflight
activate-license
matrix
build-docker (3 variants)
build-unity (matrix)
ensure-release-pr (dev push only, after all builds succeed)
```

**`release.yml`** — triggered on `push: [main]`:
```
release (single job):
  1. Find successful CI run for this SHA
  2. Download Unity build artifacts from that run
  3. Publish packages (npm + NuGet)
  4. Create per-package tags (from T1)
  5. Create release tag + GitHub Release with Unity binaries
```

### Artifact lookup mechanism

The release workflow uses the GitHub REST API to find the CI run:

```bash
SHA="${{ github.sha }}"
RUN_ID=$(gh api "/repos/{owner}/{repo}/actions/workflows/ci.yml/runs?head_sha=${SHA}&status=success" \
  --jq '.workflow_runs[0].id // empty')
```

If no successful CI run exists for the SHA (e.g., CI was red when the release PR was merged), the release workflow fails with a clear error. This is correct behavior — you shouldn't release untested code.

Artifacts are downloaded via:
```bash
gh api "/repos/{owner}/{repo}/actions/runs/${RUN_ID}/artifacts/${AID}/zip" > artifact.zip
```

This requires `actions:read` permission on the `GITHUB_TOKEN`.

### Artifact retention

GitHub Actions artifacts have a default retention of 90 days. If the release PR sits open for longer than that, the CI artifacts will have expired. This is an edge case but worth noting. Options:
- Accept it — re-run CI on dev if artifacts expired
- Increase retention for release-relevant artifacts
- The release workflow already fails clearly if artifacts aren't found

### `ensure-release-pr` consolidation

The standalone `placeframe-release-pr.yml` fires on every `push: [dev]` regardless of whether CI passed. Moving it into `ci.yml` as a job that depends on all build jobs means the release PR only reflects commits where CI was green. This is strictly better — the release PR signals "these commits are ready to release."

### Concurrency

`ci.yml` keeps the current concurrency group (cancel-in-progress for superseded runs):
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
```

`release.yml` uses a fixed group with `cancel-in-progress: false` — never abort a release mid-publish:
```yaml
concurrency:
  group: release
  cancel-in-progress: false
```

### `paths-ignore`

After T1 and T2, nothing is committed during CI or release, so `paths-ignore` becomes simpler. The only remaining case is if someone manually edits a `package.json` version field (which is now `0.0.0-local` and should never change). The `paths-ignore` list can likely be reduced or removed entirely.

### What happens to `commit` job

After T1 removes `versions.json`/`package.json` commits and T2 removes `.env.lock` commits, the `commit` job has nothing to commit. It is deleted entirely.

### What happens to `publish` job

Moves from `ci.yml` to `release.yml`. In the current workflow, `publish` runs after `build-unity` on main only. In the new structure, it runs as a step within the single `release` job, after artifacts are downloaded.

### What happens to `release` job

Moves from `ci.yml` to `release.yml`. Currently it checks out main, does `git pull --ff-only` to pick up the `commit` job's changes, downloads Unity artifacts from the same workflow run, and creates a GitHub Release. In the new structure, it downloads artifacts from the CI run (different workflow) and creates the release directly.

## Key files

**Rename/refactor:**
- `.github/workflows/placeframe.yml` → `.github/workflows/ci.yml` — change trigger to `push: [dev]`, remove `publish`/`commit`/`release` jobs, add `ensure-release-pr` job

**Create:**
- `.github/workflows/release.yml` — new workflow triggered on `push: [main]`, single `release` job that downloads CI artifacts, publishes packages, creates tags, creates GitHub Release

**Delete:**
- `.github/workflows/placeframe-release-pr.yml` — absorbed into `ci.yml` `ensure-release-pr` job

**No changes (but used by release.yml):**
- `build/src/build_scripts/placeframe/ci/publish_packages.py` — called by release workflow (already refactored in T1)
- `build/src/build_scripts/placeframe/ci/create_release.py` — called by release workflow (already refactored in T1)
- `build/src/build_scripts/placeframe/ci/ensure_release_pr.py` — called by `ensure-release-pr` job in ci.yml

## Approach

1. Rename `placeframe.yml` to `ci.yml`, change push trigger from `[main]` to `[dev]`
2. Remove `publish`, `commit`, and `release` jobs from `ci.yml`
3. Add `ensure-release-pr` job to `ci.yml` — depends on all build jobs, runs on dev push only, uses app token, runs `uv run ensure-release-pr`
4. Create `release.yml` with single `release` job: checkout main with app token, find CI run by SHA, download artifacts, run `publish-packages`, run `create-release`
5. Delete `placeframe-release-pr.yml`
6. Clean up `paths-ignore` lists (most entries no longer needed after T1/T2)

## Done when

**Verifiable now:**
- [ ] `ci.yml` triggers on `push: [dev]` and `pull_request: [main, dev]`, NOT `push: [main]`
- [ ] `ci.yml` contains: preflight, activate-license, matrix, build-docker, build-unity, ensure-release-pr
- [ ] `ci.yml` does NOT contain: publish, commit, release
- [ ] `ci.yml` `ensure-release-pr` depends on all build jobs and only runs on dev push
- [ ] `release.yml` triggers on `push: [main]`
- [ ] `release.yml` looks up successful CI run by SHA via GitHub REST API
- [ ] `release.yml` downloads Unity build artifacts from CI run
- [ ] `release.yml` runs `publish-packages` and `create-release`
- [ ] `release.yml` uses `cancel-in-progress: false`
- [ ] `release.yml` fails with clear error if no successful CI run found
- [ ] `placeframe-release-pr.yml` is deleted
- [ ] No job in either workflow creates a commit

**Requires manual verification:**
- [ ] Push to dev triggers `ci.yml` only
- [ ] Push to main triggers `release.yml` only (not `ci.yml`)
- [ ] PR to dev triggers `ci.yml` build jobs (no ensure-release-pr, no release)
- [ ] Merge release PR triggers `release.yml`, which finds CI artifacts and publishes
- [ ] `release.yml` fails cleanly when CI hasn't run for the SHA
- [ ] `ensure-release-pr` only creates/updates PR after all builds succeed

## Next step

Enter plan mode to detail the `release.yml` artifact download logic — specifically: which artifacts need downloading (Unity builds only, since Docker images are already on GHCR by SHA from T2), where they land on disk (`/tmp/release-artifacts/` per `create_release.py` expectation), and the exact `gh api` calls needed. Also decide whether `paths-ignore` can be removed entirely.
