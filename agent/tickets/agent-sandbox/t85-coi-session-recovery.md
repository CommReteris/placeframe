---
id: T85
title: Improve COI session recovery after terminal disconnect
status: design-needed
depends_on: []
---

# T85: Improve COI session recovery after terminal disconnect

## Goal

Make it possible to recover a Claude Code session after an accidental terminal close without an hour of manual forensics. The current workflow has multiple failure modes that compound into a painful recovery process.

## Context

See [incident report](t85-incident-report.md) for the full account of a real terminal disconnect and recovery.

Summary of what happened: the terminal attached to a persistent COI container (slot 1) was accidentally closed. The container kept running but the tmux session inside it was gone. Recovering the Claude Code conversation context required:

1. Backing up `.claude` directories from the still-running container
2. Discovering a host port conflict (proxy device on 5173) blocking `coi shell --resume`
3. Overriding the proxy device on a new slot via `incus config device override`
4. Restoring conversation files from root's `.claude` (not code's) into the new slot
5. Using `claude --resume` to pick the correct session

Each step required non-obvious diagnostics (`incus config show --expanded`, `ss -ltnp`, understanding COI's session cleanup behavior, knowing which user's `.claude` held the conversation store).

## Failure modes identified

1. **Persistent container != persistent interactive session.** Container survives terminal close but the tmux session does not. `coi attach` only works if tmux is still alive.

2. **Port conflicts block resume.** `coi shell --resume` creates a new container that inherits profile proxy devices. If the original slot still holds the host port, resume fails with `bind: address already in use`. The error gives no guidance on how to resolve it.

3. **Resume cleanup can overwrite session data.** COI removes old session data before saving new state during resume. A failed resume attempt could destroy the only copy of the session snapshot.

4. **Conversation store location is non-obvious.** Claude Code stores conversations under the invoking user's `~/.claude/projects/`. In our setup, Claude runs as root but the container user is `code`, so the conversation lives under `/root/.claude`, not `/home/code/.claude`. Recovery requires knowing this.

5. **`coi shell` always creates a new slot.** There's no way to say "give me a new shell in the existing container" — you get a new container or nothing.

6. **No documented recovery procedure.** The recovery required combining knowledge of Incus internals, COI session management, Claude Code's on-disk format, and our specific proxy device configuration. None of this is written down.

## Key files

- `scripts/src/scripts/agent_shell.py` — launches COI container, adds proxy devices and git mount
- `scripts/src/scripts/setup_agent_sandbox.py` — provisions Incus, builds image, configures default profile
- `agent/coi-placeframe-build.sh` — image build script

## Design directions to explore

1. **Recovery runbook** — Document the manual recovery procedure in the repo so it doesn't require re-discovery each time. Minimum viable improvement.

2. **`agent-shell --recover` subcommand** — Automate the recovery: detect running containers, back up `.claude` state, handle port conflicts, launch a new slot with restored session data, and present `claude --resume`.

3. **Prevent tmux loss** — Investigate whether tmux can be configured to survive terminal detach more reliably (e.g. `set-option -g destroy-unattached off`, or a systemd-managed tmux server inside the container).

4. **Port conflict handling in `agent_shell.py`** — When launching a new slot while an old one holds ports, auto-detect the conflict and either pick alternate ports or offer to stop the old slot.

5. **Upstream COI improvements** — File issues for: (a) `coi attach` should offer to start a new tmux session if none exists, (b) `coi shell --resume` should handle port conflicts gracefully, (c) resume cleanup should not destroy session data on failure.

## Next step

Read `agent_shell.py` and the COI source to understand which design directions are feasible within our control (1–4) vs. requiring upstream changes (5). Start with direction 3 (prevent tmux loss) since it addresses the root cause — if tmux survives terminal close, the rest of the recovery complexity goes away.

## Done when

- A terminal disconnect can be recovered from in under 5 minutes without requiring knowledge of Incus internals
- The recovery path is either automated or clearly documented
- Session data is protected from accidental destruction during recovery attempts
