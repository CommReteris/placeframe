# Pre-build Context Hashing for Docker Buildx Bake

Research conducted 2026-03-21. Context: T2 needs to tag Docker images with a deterministic content hash of their build inputs, so any checkout can compute the same hash locally and pull the right image without CI writing anything back.

## The question

Are there any prebuilt tools that can determine with 100% accuracy the exact set of files constituting the build context for a `docker buildx bake` setup and produce a deterministic pre-build content hash?

Constraints: must work with `docker buildx bake`, must be pre-build (before invoking Docker), must handle COPY instructions / .dockerignore / ARG interpolation / multi-stage builds.

## Verdict

**No.** Nothing exists that does this for buildx bake. The closest is Skaffold's Dockerfile dependency parser, which is sophisticated but embedded in Skaffold's Go codebase and doesn't integrate with bake.

## Tools evaluated

| Tool | Pre-build? | Parses Dockerfiles? | Handles ARGs? | Handles .dockerignore? | Works with bake? | Status |
|---|---|---|---|---|---|---|
| BuildKit provenance/SBOM | No (post-build) | N/A | N/A | N/A | Yes | Active |
| Skaffold `inputDigest` | Yes | Yes (sophisticated) | Yes | Yes | No ([#9586](https://github.com/GoogleContainerTools/skaffold/issues/9586)) | Active, Apache 2.0 |
| Earthly | No (internal cache only) | N/A | N/A | N/A | No (replaces Dockerfiles) | Active |
| Depot Build Insights | No (post-build) | N/A | N/A | N/A | Yes | Commercial SaaS |
| Dagger | No (internal) | N/A | N/A | N/A | No (replaces Dockerfiles) | Active, Apache 2.0 |
| `docker buildx bake --print` | Yes | No (gives context path + Dockerfile, not file list) | Resolves build args | No | Yes | Built-in |
| `docker buildx build --metadata-file` | No (post-build) | N/A | N/A | N/A | Yes | Built-in |
| BuildKit cache keys | No (internal) | Yes (internally) | Yes (internally) | Yes (internally) | Yes | Not exposed |
| `docker-source-checksum` (Rust) | Yes | Yes (basic) | **No** | Unclear | No | Abandoned (2020), 23 stars |
| `docker-image-context-hash-action` | Yes | **No** (hashes whole dir) | No | No | No | 4 stars, GH Action only |
| `docker-source-hash-action` | Yes | **No** (hashes whole dir) | No | Yes | No | 3 stars, GH Action only |
| Bazel `rules_docker` | Yes | N/A (no Dockerfiles) | N/A | N/A | No (replaces everything) | Active |
| Nix `dockerTools` | Yes | N/A (no Dockerfiles) | N/A | N/A | No (replaces everything) | Active |

## Key insights

### BuildKit already does this internally

BuildKit's `contenthash` package hashes only the files referenced by COPY/ADD instructions (not the entire context). The BuildKit client even only *sends* referenced files to the daemon. But this logic is internal — there is no API to query "what files would this build use?" without running the build.

### Skaffold's parser is the gold standard

Skaffold's `pkg/skaffold/docker/parse.go` is the most complete implementation:
- Parses COPY/ADD with the Moby buildkit parser library
- Expands ARG variables via `expandBuildArgs()`
- Tracks multi-stage `FROM ... AS` aliases and `COPY --from=` references
- Respects `.dockerignore`
- Expands glob patterns
- Processes ONBUILD triggers

It's Go, Apache 2.0, and could theoretically be extracted — but it has deep dependencies on Skaffold internals.

### The Dockerfile is inherently hard to analyze statically

Bazel and Nix achieve 100% accurate input hashing by not using Dockerfiles at all — you declare every input explicitly. Dockerfiles have runtime features (ARG interpolation, shell expansion, ONBUILD) that make static analysis imperfect.

### Python Dockerfile parsers exist

The PyPI package `dockerfile-parse` (from Red Hat, used in atomic-reactor) can parse Dockerfiles and extract COPY/ADD instructions. It handles multi-stage builds. It does NOT handle ARG interpolation in COPY source paths. For repos that don't use ARGs in COPY paths (most don't), this could be sufficient.

## Options for this project

### Option A: Manual path list (simplest)

A hardcoded `CONTEXT_PATHS` constant in Python. Single hash for all services. Exclusion-list variant errs toward extra rebuilds.

- Pro: No parsing, no edge cases, works today
- Con: Must be maintained when Dockerfiles change; can drift silently

### Option B: Parse Dockerfiles with `dockerfile-parse` (medium)

Use `docker buildx bake --print` to get each target's context/Dockerfile/args, then `dockerfile-parse` to extract COPY source paths, apply `.dockerignore`, hash the matching files.

- Pro: Automatically tracks Dockerfile changes; per-service hashes
- Con: Won't handle ARG-interpolated COPY paths (check if your Dockerfiles use any); new dependency; more code to maintain
- Mitigation: Fail loudly if a COPY source contains `$` — force manual annotation for that edge case

### Option C: Hash context directory per .dockerignore (coarse)

Hash all git-tracked files in the context dir minus `.dockerignore` patterns. Since all services use `context: .`, this produces one hash for the whole repo (minus ignored files).

- Pro: No Dockerfile parsing; respects .dockerignore
- Con: Any change to any non-ignored file triggers rebuild of all services; essentially the same as git SHA with a slightly smaller scope

### Option D: Port Skaffold's parser to Python (most accurate)

Reimplement Skaffold's Dockerfile dependency resolution in Python, including ARG expansion, multi-stage tracking, .dockerignore, and glob expansion.

- Pro: Most accurate; per-service hashes; handles edge cases
- Con: Significant implementation effort (~300-500 lines); ongoing maintenance burden; reimplementing tested Go code in Python

## Recommendation

**Option B** hits the sweet spot for this project. Check your Dockerfiles for ARG-interpolated COPY paths first — if there are none (likely), `dockerfile-parse` + `.dockerignore` + `bake --print` gives you accurate per-service hashes with reasonable effort. Fall back to Option A (single hash, manual path list) if Dockerfile parsing proves too fragile in practice.

## Sources

- [Docker Build Attestations](https://docs.docker.com/build/metadata/attestations/)
- [Skaffold Taggers](https://skaffold.dev/docs/taggers/)
- [Skaffold parse.go](https://github.com/GoogleContainerTools/skaffold/blob/main/pkg/skaffold/docker/parse.go)
- [Skaffold bake support issue #9586](https://github.com/GoogleContainerTools/skaffold/issues/9586)
- [docker buildx bake docs](https://docs.docker.com/reference/cli/docker/buildx/bake/)
- [BuildKit contenthash PR #2018](https://github.com/moby/buildkit/pull/2018)
- [dpc/docker-source-checksum](https://github.com/dpc/docker-source-checksum)
- [5monkeys/docker-image-context-hash-action](https://github.com/5monkeys/docker-image-context-hash-action)
- [matchory/docker-source-hash-action](https://github.com/matchory/docker-source-hash-action)
- [dockerfile-parse (PyPI)](https://pypi.org/project/dockerfile-parse/)
- [Depot Build Context Debugging](https://depot.dev/blog/build-context)
- [Nix Docker images](https://nix.dev/tutorials/nixos/building-and-running-docker-images.html)
