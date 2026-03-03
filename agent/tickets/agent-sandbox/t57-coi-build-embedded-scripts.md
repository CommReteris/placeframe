---
id: T57
title: "Upstream: remove repo clone once COI embeds build scripts in binary"
status: blocked
depends_on: []
---

# T57: Upstream: remove repo clone once COI embeds build scripts in binary

## Goal

Track the upstream fix for [mensfeld/code-on-incus#50](https://github.com/mensfeld/code-on-incus/issues/50) — `coi build` currently requires the repo to be cloned locally because build scripts aren't embedded in the binary. Once a release ships with embedded scripts, simplify `setup_agent_sandbox.py`.

## Context

Issue #50 was closed but the underlying problem (build scripts not embedded) was not fixed — it was closed alongside PR #58 which addressed a different issue (Colima/Lima detection). The repo clone (`clone_or_update_coi_repo()`, `COI_REPO_DIR`, and `cwd=COI_REPO_DIR` on build calls) is still required.

## Blocked on

A new COI release that embeds build scripts in the binary, eliminating the need for the cloned repo.

## Key files

- `scripts/src/scripts/setup_agent_sandbox.py` — `clone_or_update_coi_repo()`, `COI_REPO_DIR`, `cwd=` on build calls

## Done when

- [ ] New COI release ships with embedded build scripts
- [ ] Remove `clone_or_update_coi_repo()` from `setup_agent_sandbox.py`
- [ ] Remove `COI_REPO_DIR` constant and `cwd=` arguments from build calls
- [ ] Update `COI_BINARY_URL` to the release that includes the fix
