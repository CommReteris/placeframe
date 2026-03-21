## Implementation Plan: T2 — Tree-SHA Image References via `.dockerignore` Allowlist

### Context

CI builds Docker images, writes their digests to `.env.lock`, and commits back. This violates the CI commit-free invariant. The solution: tag images with `tree-<sha>` where the SHA is a `git write-tree` hash of all files visible to Docker (as defined by `.dockerignore`). Any checkout computes the same hash locally.

### Current branch state

The branch (`feature/ci-refactor`) has a working but overly complex per-service Dockerfile-parsing implementation. This plan replaces it with a simpler `.dockerignore`-allowlist approach.

**Reusable as-is:**
- `.env.lock` — already stripped of built-image entries
- `commit_artifacts.py` — already deleted
- CI `commit` job — already removed from `placeframe.yml`
- `tag-built` job — already removed from `test-t2.yml`
- Test workflow `test-t2.yml` — exists for CI iteration

**Needs simplification:**
- `context_sha.py` — replace Dockerfile-parsing + bake-print logic with git-ls-files + pathspec + write-tree
- Compose files (`compose.yml`, `compose.cuda.yml`, `compose.rocm.yml`) — revert 11 per-service vars to single `${CONTEXT_SHA:?err}`
- `compose.bake.yml` — revert per-target vars to single `${CONTEXT_SHA}`
- `build_docker.py` — single `CONTEXT_SHA` instead of per-service loop
- `up.py` / `down.py` — single `CONTEXT_SHA` instead of per-service

**Needs deletion:**
- `dockerfile_parse_utils.py`
- `lint_dockerfiles.py`
- `build/tests/test_dockerfile_parse_utils.py`
- `build/tests/test_lint_dockerfiles.py`
- `dockerfile-parse` dependency from `build/pyproject.toml`
- Dockerfile lint step from `preflight.py`

**Needs creation/rewrite:**
- `.dockerignore` — convert to allowlist format

### Approach

**Step 1: Rewrite `.dockerignore` as an allowlist**

Current `.dockerignore` is an exclusion list (ignores build artifacts, secrets). Rewrite to:

```
# Ignore everything, then allowlist only what Docker builds need.
# Adding a COPY for a path not listed here will fail the build loudly.
*
!docker/
!packages/
!legacy/
!pyproject.toml
!uv.lock
!compose.bake.yml
```

Determine the correct allowlist by checking all COPY/ADD sources across all `docker/*/Dockerfile` files. The previous session already extracted these (see ticket's design decisions). Key paths:
- `docker/` — all Dockerfiles and service code
- `packages/` — shared Python packages (common, core, neural-networks, generated clients)
- `legacy/` — .NET code (state-sync service)
- `pyproject.toml` — root project config (some Dockerfiles may reference it)
- `uv.lock` — dependency pins
- `compose.bake.yml` — build configuration (included in hash, not COPYed)

Verify: run `docker buildx bake --print` and then `docker buildx bake` with `--load` for at least one service to confirm the allowlist doesn't break builds.

**Step 2: Simplify `context_sha.py`**

Rewrite to:

```python
def compute_context_sha(repo_root: Path) -> str:
    # Get all git-tracked files
    all_files = subprocess.run(
        ["git", "ls-files"], cwd=str(repo_root),
        capture_output=True, text=True, check=True
    ).stdout.splitlines()

    # Filter through .dockerignore (keep files Docker can see)
    dockerignore = repo_root / ".dockerignore"
    spec = pathspec.PathSpec.from_lines("gitwildmatch", dockerignore.read_text().splitlines())
    visible_files = [f for f in all_files if not spec.match_file(f)]

    # Compute tree SHA from visible files
    with TemporaryDirectory() as tmpdir:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(tmpdir) / "index")}
        subprocess.run(["git", "add", "--"] + visible_files, cwd=str(repo_root), env=env, ...)
        result = subprocess.run(["git", "write-tree"], cwd=str(repo_root), env=env, ...)
        return f"tree-{result.stdout.strip()}"
```

Delete `compute_context_shas` (plural), `env_var_name`, `_normalize_target_name`. The module exports one function: `compute_context_sha(repo_root) -> str`.

Remove the import of `dockerfile_parse_utils`.

**Step 3: Delete Dockerfile parsing code**

- Delete `build/src/build_scripts/placeframe/dockerfile_parse_utils.py`
- Delete `build/src/build_scripts/placeframe/lint_dockerfiles.py`
- Delete `build/tests/test_dockerfile_parse_utils.py`
- Delete `build/tests/test_lint_dockerfiles.py`
- Remove `dockerfile-parse` from `build/pyproject.toml` dependencies (keep `pathspec`)
- Remove Dockerfile lint step from `build/src/build_scripts/placeframe/ci/preflight.py`

**Step 4: Update compose files — single `CONTEXT_SHA`**

Replace all per-service variables with single `${CONTEXT_SHA:?err}`:

In `compose.yml`:
```yaml
api:
  image: "ghcr.io/.../api:${CONTEXT_SHA:?err}"
```

In `compose.bake.yml`:
```yaml
api:
  build:
    tags:
      - "ghcr.io/.../api:latest"
      - "ghcr.io/.../api:${CONTEXT_SHA}"
```

Same for `compose.cuda.yml`, `compose.rocm.yml`.

**Step 5: Update `build_docker.py`**

Replace:
```python
from .context_sha import compute_context_shas, env_var_name
context_shas = compute_context_shas(BAKE_FILE, Path.cwd())
for target, sha in context_shas.items():
    os.environ[env_var_name(target)] = sha
```

With:
```python
from .context_sha import compute_context_sha
os.environ["CONTEXT_SHA"] = compute_context_sha(Path.cwd())
```

Update local lock file write: single `CONTEXT_SHA=<hash>` instead of per-service entries.

**Step 6: Update `up.py` and `down.py`**

Replace `_load_lock_values` (suffix matching) with simple key lookup for `CONTEXT_SHA`. Replace `compute_context_shas` call with `compute_context_sha`.

**Step 7: Write tests**

Test `compute_context_sha`:
- Deterministic (same inputs → same hash)
- Test the pathspec filtering against a mock `.dockerignore` with allowlist patterns

**Step 8: Verify**

1. `uv run ruff check .`, `uv run ruff format --check .`, `uv run basedpyright`, `uv run pytest`
2. Compute context SHA locally, confirm it's stable across invocations
3. Push to trigger `test-t2.yml` — verify CI build succeeds
4. Pull a CI-built image by its tree-SHA tag locally
5. Confirm a non-Docker change (edit a `.md`) doesn't change the SHA

### Key files

**Create/rewrite:**
- `.dockerignore` — allowlist format

**Simplify:**
- `build/src/build_scripts/placeframe/context_sha.py` — single `compute_context_sha` function
- `build/src/build_scripts/placeframe/build_docker.py` — single `CONTEXT_SHA`
- `build/src/build_scripts/placeframe/up.py` — single `CONTEXT_SHA`
- `build/src/build_scripts/placeframe/down.py` — single `CONTEXT_SHA`
- `compose.yml` — single `${CONTEXT_SHA:?err}`
- `compose.cuda.yml` — same
- `compose.rocm.yml` — same
- `compose.bake.yml` — single `${CONTEXT_SHA}` in tags

**Delete:**
- `build/src/build_scripts/placeframe/dockerfile_parse_utils.py`
- `build/src/build_scripts/placeframe/lint_dockerfiles.py`
- `build/tests/test_dockerfile_parse_utils.py`
- `build/tests/test_lint_dockerfiles.py`

**Modify:**
- `build/pyproject.toml` — remove `dockerfile-parse` dependency
- `build/src/build_scripts/placeframe/ci/preflight.py` — remove Dockerfile lint step

### Open questions

1. **`pyproject.toml` in allowlist**: Do any Dockerfiles COPY `pyproject.toml`? Check before including. If not, omit.
2. **`compose.bake.yml` in hash**: Including it means changing build config (e.g., adding a new target) changes the hash. This is arguably correct — new targets could mean new images.
3. **`pathspec` vs Docker behavior**: Verify that `pathspec`'s `gitwildmatch` handles the `*` + `!` negation pattern identically to Docker's `.dockerignore` parser. Both follow gitignore semantics but test to be sure.
