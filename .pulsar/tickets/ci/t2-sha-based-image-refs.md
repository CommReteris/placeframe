---
id: T2
title: Replace .env.lock built-image digests with tree-SHA image tags
status: done
constraint: build/src/build_scripts/placeframe/ci/CLAUDE.md#ci-commit-free-invariant
violators: []
depends_on: []
plan: t2-plan.md
---

Built-image digests are stored in `.env.lock` and committed by `commit_artifacts.py`. Compose files reference built images via `${SERVICE_IMAGE:?err}` from `.env.lock`. This violates the CI commit-free invariant.

## Design decisions

### Why not commit-SHA tags?

The first approach was to tag images with the git commit SHA (`service:<commit-sha>`). This works for CI but breaks the local workflow: after `uv run build` + new commits + `uv run up`, HEAD has moved to a SHA with no images. Any checkout of a commit where CI didn't run also has no images.

The core problem: a fresh checkout needs to know which SHA has images on GHCR, but CI can't write that information back to the branch.

### Why not git tags as markers?

The second approach was CI pushing a `built-<sha>` git tag after building, then `up.py` using `git describe --tags --match='built-*'` to find the nearest ancestor with images. This works but is a novel pattern with no established convention, and the tag naming felt arbitrary.

### Why not Dockerfile parsing for per-service hashes?

We researched whether any tool (BuildKit, Skaffold, Earthly, Depot, Dagger, standalone tools) could determine exactly which files a `docker buildx bake` build uses per service. None can. BuildKit computes this internally (`FollowPaths` in the LLB solver) but does not expose it — [moby/buildkit#1181](https://github.com/moby/buildkit/issues/1181) has been open since 2019, a [draft PR#4071](https://github.com/moby/buildkit/pull/4071) was abandoned, and the maintainer called it "not very interesting" ([#1655](https://github.com/moby/buildkit/issues/1655)).

We built a working implementation using `dockerfile-parse` (PyPI) to extract COPY/ADD sources from Dockerfiles, plus a CI lint to ban ARG-interpolated COPY paths. It worked, but the code was complex (~150 lines of parsing logic) and fragile — reimplementing what BuildKit already knows. Code is a liability; more code for a build system is a bigger liability.

Research: `.pulsar/research/build-context-hashing-tools.md`

### Why not a manual path list?

A manually maintained list of which directories affect Docker builds (e.g., `CONTEXT_PATHS = ["docker/", "packages/", ...]`) drifts silently. If someone adds a COPY for a new path but forgets the list, images become stale — subtle and hard to diagnose. An exclusion list (hash everything except known-irrelevant dirs) is safer but still requires maintenance.

### Final approach: `.dockerignore` allowlist + `git write-tree`

Convert `.dockerignore` to an allowlist format:

```
*
!docker/
!packages/
!legacy/
!pyproject.toml
!uv.lock
!compose.bake.yml
```

`*` ignores everything, then `!` lines whitelist paths Docker can see. This is standard `.dockerignore` syntax.

Then compute a single `CONTEXT_SHA` by:
1. `git ls-files` — all tracked files
2. Filter through `.dockerignore` patterns via `pathspec` (same gitignore semantics Docker uses)
3. `git add` survivors to a temp index, `git write-tree` — deterministic tree SHA
4. Tag images as `tree-<sha>`

**Why this works:**
- `.dockerignore` is the single source of truth for what Docker can see during builds
- If someone adds a COPY for a path not in the allowlist, the build fails loudly (Docker can't see the file) — self-correcting drift
- If someone removes a COPY but forgets to update `.dockerignore`, extra rebuilds occur — safe failure mode
- Single hash for all images — layer caching handles redundant rebuilds
- ~15 lines of code: `git ls-files` + pathspec filter + `git write-tree`
- No Dockerfile parsing, no `bake --print`, no per-service complexity
- Deterministic, cross-machine, computable from any checkout instantly

**Properties preserved:**
- **CI commit-free**: CI computes hash from checkout, tags images, pushes. No commits.
- **Repo is source of truth**: `.dockerignore` + tracked files = deterministic hash
- **Survives unrelated commits**: `unity/` not in allowlist → hash unchanged → same images
- **Historical reproducibility**: old checkout has old `.dockerignore` + old files → same hash
- **Clone and `uv run up` without building**: computes hash, pulls from GHCR

## Approach

See `.pulsar/plans/t2-plan.md` for full implementation plan.

Summary: Rewrote `.dockerignore` as allowlist. Simplified `context_sha.py` to ~15 lines (git ls-files + pathspec + write-tree, single hash). Reverted compose files from 11 per-service vars to single `${CONTEXT_SHA:?err}`. Deleted `dockerfile_parse_utils.py`, `lint_dockerfiles.py`, and their tests. Removed `dockerfile-parse` dep. Removed Dockerfile lint from preflight.

## Log

- `legacy/Outernet.Client/` was included by `!legacy/` allowlist, causing arg list overflow in `git add`. Fixed by re-ignoring `legacy/Outernet.Client/` in `.dockerignore`.
- `git add` to temp index failed because `.gitignore`-ignored files (tracked in main index) were rejected. Fixed with `--force` flag.
- `pathspec` library deprecated `gitwildmatch` pattern name. Fixed by using `gitignore`.
- Used `--pathspec-from-file` instead of passing file list as args to avoid OS arg length limits.

## Observations

- Unit tests for `compute_context_sha` use toy repos and don't exercise `--force` or `--pathspec-from-file` code paths that were needed on the real repo. A pytest that validates real `.dockerignore` against real Dockerfile COPY paths would catch allowlist drift early.
- `up.py`/`down.py` `_resolve_context_sha` has no test coverage.
- `test-t2.yml` workflow should be deleted before merging to dev.
