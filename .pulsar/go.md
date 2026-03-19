# Go Brief: T104 — validate unified CI workflow

## Situation

T104 (unify CI preflight) is on `feature/ci-cd`. Three CI issues diagnosed and fixed:
1. **tqdm missing** from neural-networks (stale pylock, fixed in earlier commit)
2. **git exit code 129** in `check_tracked_files` — `actions/checkout` sets `safe.directory` in a temporary HOME that's deleted after the step (actions/checkout#766). Fixed: `setup-job` now re-sets it. Also removed `verbose_errors=False` that was hiding this error.
3. **NuGet packages not restored** in `unity-preflight` — Newtonsoft.Json, Polly, JsonSubTypes are managed by NuGetForUnity and gitignored. The `build-unity` job restored them but `unity-preflight` didn't. Fixed: added `dotnet tool restore` + `dotnet nugetforunity restore` loop before `lock-packages --check`.

Also created T106 (split `run_command` into four named functions) — deferred, not blocking.

## What to do

1. Push and trigger CI
2. Check CI run — confirm all jobs pass (preflight, build-docker, unity-preflight, build-unity)
3. If CI passes: ask user to update branch protection required status check `Build / build-and-lock` → `CI / build-docker`
4. Merge to main, move T104 to done

## Host checklist

- Push the branch (sandbox token is read-only)
- Update branch protection settings in GitHub repo config after CI passes
