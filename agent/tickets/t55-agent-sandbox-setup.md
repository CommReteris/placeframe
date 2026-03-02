---
id: T55
title: Rewrite agent sandbox setup in Python and add worktree support
status: ready
depends_on: []
plan: t55-plan.md
---

# T55: Rewrite agent sandbox setup in Python and add worktree support

## Goal

Move the COI (Code on Incus) sandbox provisioning logic from `agent/setup.sh` into a Python script in `scripts/`, and create a `coi-shell` Python wrapper that transparently handles git worktrees by mounting the main `.git` directory into the container.

## Context

### Current state

`agent/setup.sh` is a 199-line bash script that provisions the host for running Claude Code inside Incus containers via COI (Code on Incus). It:

1. Installs host dependencies (git, firewalld, btrfs-progs, uidmap)
2. Configures firewalld with a dedicated `incus` zone
3. Sets up subuid/subgid mappings for unprivileged containers
4. Installs Incus from the Zabbly repo
5. Initializes Incus with preseed (btrfs storage pool, bridge network)
6. Configures firewall rules for the Incus bridge
7. Adds GPU passthrough to the Incus default profile
8. Installs the COI binary from GitHub releases
9. Clones the COI repo and builds the base image
10. Builds a project-specific `coi-placeframe` image via `agent/coi-placeframe-build.sh`
11. Writes COI user config (`~/.config/coi/config.toml`)
12. Propagates host git identity into the Incus default profile
13. Sets `UV_PROJECT_ENVIRONMENT` in the Incus default profile

`agent/coi-placeframe-build.sh` runs inside a temporary container during image build. It installs uv, Node.js 20, pnpm, Playwright Chromium, and configures git safe.directory.

### Why rewrite in Python

The project convention is to keep scripts in `scripts/src/scripts/` as Python, registered in `scripts/pyproject.toml` and run via `uv run <command>`. Bash scripts are harder to review, test, and maintain. The setup logic is purely orchestration (running system commands, writing config files, checking state) — all straightforward to express in Python using `run_command` from `common.run_command`.

### The worktree problem

When an engineer creates a git worktree and runs `coi shell` from it, git operations inside the container fail:

```
fatal: not a git repository: /home/tyler/Repos/placeframe/.git/worktrees/ci-improvements
```

**Root cause:** A git worktree's `.git` is a file (not a directory) containing a `gitdir:` pointer to the main repo's `.git/worktrees/<name>` directory. That absolute host path doesn't exist inside the container. The worktree metadata also has a `commondir` reference back to the main `.git` for shared objects/refs, so the entire main `.git` directory must be reachable.

**Why it can't be fixed in setup.sh alone:** The mount decision is dynamic — it depends on where the engineer cloned the repo and which worktree they're in. COI doesn't expose a pre-launch hook. The extra mount must be added at `coi shell` launch time, not at provisioning time.

**Solution:** A `coi-shell` wrapper that detects worktrees and adds an extra Incus disk device for the main `.git` directory before launching the container.

### COI mount architecture (research)

COI uses Incus disk devices to mount host directories into containers:

- **Workspace mount:** `coi shell` mounts the current directory at `/workspace` by default. The `--workspace PATH` flag overrides this.
- **Additional mounts via config:** `.coi.toml` (project-level) or `~/.config/coi/config.toml` (user-level) support a `[mounts]` section:
  ```toml
  [mounts]
  default = [
    { host = "/some/path", container = "/mount/point" }
  ]
  ```
  But these are static paths, useless for dynamic worktree detection.
- **Incus disk devices directly:** `incus config device add <container> <name> disk source=<host> path=<container> shift=true` — this is what the wrapper would use.
- **Protected paths:** COI auto-mounts `.git/hooks` and `.git/config` as read-only for security. It already has `.git`-awareness, so worktree detection would be a natural extension (potential upstream feature request).
- **UID shifting:** Incus handles UID/GID mapping automatically via the `shift` parameter on disk devices.
- **`preserve_workspace_path`:** COI config option to mount at the host path instead of `/workspace` — not useful here since we need the main `.git` at its host path regardless.

### Worktree wrapper approach

When launched from a worktree:

1. Detect: `.git` is a file, not a directory
2. Parse: `sed 's/gitdir: //' .git` → e.g. `/home/tyler/Repos/placeframe/.git/worktrees/ci-improvements`
3. Resolve main `.git`: `git rev-parse --git-common-dir` → e.g. `/home/tyler/Repos/placeframe/.git`
4. Launch `coi shell` normally (mounts worktree at `/workspace`)
5. Add disk device: `incus config device add <container> main-git disk source=<main-.git> path=<main-.git> shift=true`
6. Add safe.directory for the main `.git` path in the container's git config

When launched from a normal repo (`.git` is a directory), pass through to `coi shell` unchanged.

### Design decisions (settled)

- **uv is a host prerequisite.** No bash bootstrap shim needed. The setup script is a Python script run via `uv run setup-sandbox`.
- **`coi-placeframe-build.sh` stays as bash.** COI's `coi build custom --script` requires a bash script. This file is 10 lines and runs inside a throwaway container — not worth abstracting.
- **`coi-shell` is a Python script** registered as `uv run coi-shell`. It detects worktrees, adds the extra Incus disk device, and delegates to `coi shell`. When not in a worktree, it passes through unchanged.
- **`agent/setup.sh` is deleted** and replaced by `scripts/src/scripts/setup_sandbox.py`. The `coi-placeframe-build.sh` stays in `agent/` since it's referenced by the setup script during image build.

## Approach

Two new Python scripts replace `agent/setup.sh` and add worktree support. `setup_sandbox.py` is a Typer-based script that translates each section of the bash script into an idempotent function, called in order. `coi_shell.py` is a direct-main wrapper that detects worktrees via `git rev-parse --git-common-dir`, adds an Incus disk device for the main `.git` directory to the container, then delegates to `coi shell`. For non-worktree repos it's a pure passthrough via `exec_command`.

## Key files

- `agent/setup.sh` — delete (replaced by Python)
- `agent/coi-placeframe-build.sh` — keep as-is (COI requires bash)
- `scripts/src/scripts/setup_sandbox.py` — new: host provisioning logic
- `scripts/src/scripts/coi_shell.py` — new: coi shell wrapper with worktree support
- `scripts/pyproject.toml` — register `setup-sandbox` and `coi-shell` commands

## Done when

- `uv run setup-sandbox` provisions the host identically to the current `agent/setup.sh`
- `uv run coi-shell` launches a COI container; when run from a worktree, it mounts the main `.git` directory so git works inside the container
- `uv run coi-shell` from a non-worktree repo works identically to bare `coi shell`
- `agent/setup.sh` is deleted
- `agent/coi-placeframe-build.sh` still works (referenced by setup-sandbox during image build)
- Both new scripts are registered in `scripts/pyproject.toml`
