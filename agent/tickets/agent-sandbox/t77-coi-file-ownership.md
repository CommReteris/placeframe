---
id: T77
title: Fix COI container file ownership so host user can write
status: design-needed
depends_on: []
---

# T77: Fix COI container file ownership so host user can write

## Goal

Files created by Claude Code inside the COI container must be writable by the host user. Currently they end up owned by root, breaking host-side git operations (rebase, checkout, etc.).

## Context

Claude Code runs as `root` (UID 0) inside the Incus system container. The workspace is bind-mounted from the host, where files are owned by `code` (UID 1000). The container's UID map is `0 → 100000`, so container root maps to host UID 100000 — not to 1000. Every file Claude creates or modifies becomes `root:root` inside the container, which appears as `100000:100000` (or just inaccessible) on the host.

The mount shows `idmapped` in `/proc/mounts`, and COI presumably sets this up, but the mapping doesn't produce the right host UID. Meanwhile, the worktree git mount added by `agent_shell.py` uses `shift=true` on its Incus disk device, which does work correctly.

Current workaround: `sudo chown -R $(id -u):$(id -g) .` on the host after each session. This is tedious and easy to forget.

## Key files

- `scripts/src/scripts/agent_shell.py` — launches COI container, adds git mount with `shift=true`
- `scripts/src/scripts/setup_agent_sandbox.py` — provisions Incus, builds image, configures default profile
- `agent/coi-placeframe-build.sh` — image build script (sets `safe.directory` but not ownership)

## Approach

Investigate two directions:

1. **COI configuration** — does COI support `shift=true` or equivalent on its workspace mount? Check COI docs/source for disk device options.
2. **Incus profile override** — add a disk device to the default profile that mounts `/workspace` with `shift=true`, overriding COI's mount. The git worktree mount in `agent_shell.py` already proves this mechanism works.

Fallback: run Claude Code as UID 1000 (`code`) instead of root inside the container, or add a post-session chown hook.

## Done when

- Files created by Claude Code inside the container are writable by the host user (UID 1000) without manual chown
- Existing `agent_shell.py` git mount (with `shift=true`) continues to work
- No regression in Unity license activation or other container setup
