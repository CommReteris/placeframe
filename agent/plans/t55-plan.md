# T55 Plan: Rewrite agent sandbox setup in Python and add worktree support

## Context

`agent/setup.sh` is a 199-line bash script that provisions hosts for running Claude Code inside Incus containers via COI. The project convention is Python scripts in `scripts/src/scripts/`, run via `uv run <command>`. Additionally, `coi shell` doesn't work from git worktrees because the main `.git` directory isn't mounted. A wrapper script solves this.

## Approach

### 1. Create `scripts/src/scripts/setup_sandbox.py`

Typer-based script (Pattern A, matching `up.py`/`build.py`) with a `--rebuild` flag. Each section of `setup.sh` becomes a function, called in order from the Typer command.

Functions (in execution order):
1. `install_host_dependencies()` — apt install ca-certificates, curl, git, firewalld, btrfs-progs, uidmap
2. `configure_firewalld()` — disable ufw, enable firewalld, write sudoers rule, create incus zone
3. `ensure_subuid_subgid()` — append `root:100000:65536` to /etc/subuid and /etc/subgid if missing
4. `install_incus()` — install from Zabbly repo if not present, add user to incus-admin, exit with message if group not yet active
5. `initialize_incus()` — preseed init (btrfs pool, bridge network) only if "default" pool doesn't exist
6. `configure_firewall_rules()` — add incusbr0 to incus zone, enable NAT/DHCP/DNS, reload
7. `add_gpu_passthrough()` — add gpu device to default profile if not present
8. `install_coi_binary()` — download from GitHub releases to /usr/local/bin/coi
9. `clone_or_update_coi_repo()` — clone to /opt/code-on-incus or `git pull --ff-only`
10. `build_base_image()` — `coi build` from COI repo if `coi` image doesn't exist
11. `build_placeframe_image(rebuild)` — delete image if --rebuild, build via `coi build custom coi-placeframe --script agent/coi-placeframe-build.sh` if image doesn't exist
12. `write_coi_config()` — write `~/.config/coi/config.toml` with persistent=true, image=coi-placeframe
13. `propagate_git_identity()` — read host git config, set GIT_AUTHOR_*/GIT_COMMITTER_* on Incus default profile (warn if not set)
14. `set_uv_project_environment()` — set UV_PROJECT_ENVIRONMENT on Incus default profile

Error handling: `run_command` raises on failure by default. Idempotent commands (zone creation, device additions) use `try/except CalledProcessError` to match the `|| true` pattern from bash. The group membership gate calls `sys.exit(0)` with an informational message.

### 2. Create `scripts/src/scripts/coi_shell.py`

Direct `main()` pattern (no Typer — needs to forward arbitrary args to `coi shell` without parsing them).

Functions:
1. `detect_worktree() -> Path | None` — check if `.git` is a file; if so, run `git rev-parse --git-common-dir` and return resolved main `.git` path
2. `compute_container_name(workspace: Path, slot: int = 1) -> str` — replicate COI's naming: `coi-{sha256(str(workspace))[:8]}-{slot}`
3. `container_exists(name: str) -> bool` — `check_command(f"incus info {name}")`
4. `add_git_mount(container_name: str, main_git_path: Path)` — `incus config device add <name> main-git disk source=<path> path=<path> shift=true` (idempotent, ignore "already exists"). Also add `safe.directory` for the main repo path via `incus exec <name> -- git config --system --add safe.directory <parent>`
5. `main()` — entry point with two paths:
   - **Not a worktree**: `exec_command("coi shell ...")` — pure passthrough
   - **Worktree, container exists**: `add_git_mount()`, then `exec_command("coi shell ...")`
   - **Worktree, container doesn't exist (first launch)**: run `coi shell` as subprocess with a background thread that polls for container readiness and calls `add_git_mount()` once running. Forward SIGINT/SIGTERM to the subprocess. Exit with its return code.

### 3. Register both in `scripts/pyproject.toml`

Add:
```toml
setup-sandbox = "scripts.setup_sandbox:main"
coi-shell = "scripts.coi_shell:main"
```

### 4. Delete `agent/setup.sh`

### 5. Update `CLAUDE.md`

Line 99 references `agent/setup.sh` — update to say "the Incus default profile (configured by `uv run setup-sandbox`)".

## Key files

| File | Action |
|---|---|
| `scripts/src/scripts/setup_sandbox.py` | Create — host provisioning |
| `scripts/src/scripts/coi_shell.py` | Create — worktree-aware coi shell wrapper |
| `scripts/pyproject.toml` | Modify — register both commands |
| `agent/setup.sh` | Delete |
| `CLAUDE.md` | Modify — update setup.sh reference |
| `agent/coi-placeframe-build.sh` | Keep unchanged |
| `packages/python/common/src/common/run_command.py` | Read-only reference — `run_command`, `exec_command`, `check_command` |

## Verification

- `uv run ruff check scripts/src/scripts/setup_sandbox.py scripts/src/scripts/coi_shell.py`
- `uv run ruff format --check scripts/src/scripts/setup_sandbox.py scripts/src/scripts/coi_shell.py`
- `uv run basedpyright scripts/src/scripts/setup_sandbox.py scripts/src/scripts/coi_shell.py`
- Confirm `uv run setup-sandbox --help` and `uv run coi-shell --help` work
- Full provisioning and worktree testing require a host with Incus (manual verification)
