# T85 Incident Report: Terminal Disconnect Recovery

Incident date: 2026-03-05

## Incident summary

Accidentally closed the terminal attached to a **persistent COI container** (`coi-68806bbe-1`, slot 1) that was still running. Needed to get back to the **in-progress Claude Code session with full context** without killing the container (because it was "parked" on a host port) and without triggering Claude onboarding.

The core outcome:

* The **interactive session was not reattachable** because COI reported **no tmux sessions** in the running container (`no sessions`).
* The **conversation/context was not lost** because Claude Code stores it on disk under `.claude/` (projects JSONL, history JSONL).
* Recovery steps:

  1. **Back up Claude state** from the running container.
  2. **Resume into a new slot** (slot 5), fixing a **host port collision** (5173 already in use).
  3. Restore the correct `.claude` conversation store into the resumed container (needed because the conversation was in root's `.claude` backup, not code's).
  4. Use `claude --resume` to select the correct session snapshot and get back in.

---

## Environment and constraints

### Architecture

* Tooling: `code-on-incus` (COI) orchestrating Incus containers.
* Host workspace: `/home/tyler/repos/placeframe/base`
* Container user: `code`
* Container workspace mount: `/workspace` — mapped from host path
* Target original container: `coi-68806bbe-1` (slot 1), **persistent**, still running.
* A host port was occupied (127.0.0.1:5173) by Incus (`incusd` listener). This was a hard constraint: did not want to kill slot 1 and lose whatever service was bound there.

### Operational constraints

* Needed to reattach without destroying slot 1.
* Needed to avoid "new user onboarding" inside Claude Code (a symptom that credentials/config were missing).
* The wrapper script's behavior (launching `coi shell`) would always try to create a new slot if an occupied slot existed, so rerunning it could not restore the old session.

---

## Root cause analysis

### 1) Why "reattach the same session" failed

`coi attach --slot 1` reported:

* `Attaching to coi-68806bbe-1 (slot 1)...`
* `no sessions`
* `No tmux session found in container. The container is still running...`

The **tmux multiplexer session inside the container had ended** (either the tmux server was never started, crashed, or exited when the terminal died). COI's attach mechanism can only restore the exact same interactive shell if tmux is present; without it, the interactive Claude UI process is gone.

### 2) Why "incus exec ... su - code" caused Claude onboarding

Direct Incus exec bypassed COI's credential and config injection. Running `claude -c` caused Claude onboarding because the shell environment lacked COI-injected auth state.

### 3) Why "coi shell --resume" initially failed

`coi shell --resume` correctly detected a saved session ID and tried to create a new slot/container. It failed with:

* `Failed to listen on 127.0.0.1:5173: bind: address already in use`

Slot 1 already had a host-level binding on `127.0.0.1:5173` (owned by `incusd`). COI's resumed container inherited a proxy device (`type: proxy`) trying to bind the same host listen port.

### 4) COI resume cleanup can overwrite session data

During resume attempts, COI printed cleanup messages indicating it removes old session data before saving new state. This raised a credible risk that a failed/empty resume could overwrite the persisted session snapshot.

---

## Everything tried (chronological order)

### Attempt A — rerun wrapper script

* Command: `uv run agent-shell`
* Outcome: started a new container/slot, not slot 1.
* Reason: wrapper invokes `coi shell --image ...` without targeting an existing occupied slot.

### Attempt B — raw Incus shell

* Command: `incus exec coi-68806bbe-1 -- su - code`
* Outcome: shell access ok, but `claude -c` triggered onboarding.
* Reason: bypassed COI's injected credentials/config.

### Attempt C — target slot directly with `coi shell`

* Command: `coi shell --slot 1 --image coi-placeframe`
* Outcome: COI refused occupied slot 1, auto-allocated slot 4.
* Reason: `coi shell` intentionally refuses to overwrite a running slot.

### Attempt D — `coi attach --slot 1`

* Output: `no sessions` / `No tmux session found in container.`
* Outcome: confirmed interactive session was not reattachable.

### Attempt E — `coi shell --resume` (first time)

* Outcome: failed with `bind: address already in use` on `127.0.0.1:5173`.

---

## The fix (step-by-step)

### Step 1 — Back up Claude state from slot 1

```bash
mkdir -p ~/tmp/coi-slot1-backup
coi file pull -r coi-68806bbe-1:/root/.claude ~/tmp/coi-slot1-backup/root-dot-claude
coi file pull -r coi-68806bbe-1:/home/code/.claude ~/tmp/coi-slot1-backup/code-dot-claude
```

### Step 2 — Confirm port conflict

```bash
sudo ss -ltnp | grep ':5173'
# LISTEN ... 127.0.0.1:5173 ... users:(("incusd",pid=7020,fd=...))
```

Port owned by Incus daemon — proxy device from slot 1.

### Step 3 — Identify proxy device on resume container

```bash
incus config show coi-68806bbe-5 --expanded | sed -n '/^devices:/,/^[^ ]/p'
```

Found `board-dev` device: `type: proxy`, `listen: tcp:127.0.0.1:5173`, `connect: tcp:127.0.0.1:5173`.

### Step 4 — Override host listen port

```bash
incus config device override coi-68806bbe-5 board-dev listen=tcp:127.0.0.1:5174
```

### Step 5 — Back up COI session snapshot

```bash
SESSION=0a689ef5-459c-4fb1-8e7a-9a3d5b3b1285
cp -a ~/.coi/sessions-claude/$SESSION ~/.coi/sessions-claude/${SESSION}.bak.$(date +%s)
```

### Step 6 — Resume into slot 5

```bash
coi shell --resume=0a689ef5-459c-4fb1-8e7a-9a3d5b3b1285 --slot 5
```

### Step 7 — Restore conversation store

Conversation files were in `/root/.claude/projects/-workspace/*.jsonl` (root's home, not code's). Copied from backup into the resumed container's expected location.

### Step 8 — Resume Claude session

```bash
claude --resume
```

Selected the correct session from the picker and regained working context.

---

## Lessons learned

1. **Persistent container != persistent interactive session.** Container survives while tmux dies. `coi attach` only works with a live tmux session.

2. **Always treat `coi shell` as "start new," `coi attach` as "reattach."** `coi shell` against an occupied slot gives a new slot, not the existing one.

3. **Port conflicts during resume are Incus proxy devices.** If `incusd` owns the port, look for `type: proxy` devices in expanded config and override per-instance.

4. **Use `incus config show --expanded` for inherited devices.** `incus config device show` hides profile-inherited devices.

5. **Back up `.claude` immediately.** Claude Code conversation logs are stored on disk (JSONL). Even if interactive state is gone, conversation context is recoverable. Root's `.claude` was the critical store.

6. **Be cautious with COI resume cleanup.** COI can remove old session data before saving a new snapshot; back up `~/.coi/sessions-claude/<session-id>` before retrying.

7. **Session selection is reversible.** `claude --resume` can be re-run; selecting one entry is not a one-way door.
