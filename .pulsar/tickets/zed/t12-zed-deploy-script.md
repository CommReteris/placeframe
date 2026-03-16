---
id: T12
title: Zero-internet ZED deployment script
status: in-review
depends_on: [T10]
---

# T12: Zero-internet ZED deployment script

## Goal

`uv run deploy-rig` script that bridges the user's internet-connected host to the air-gapped ZED Box over the USB gadget link at `192.168.55.1`.

## Context

The ZED Box has no internet access. Currently deployment is manual. This script automates the full flow: probe the Jetson's L4T version, pull the correct Docker image on the host, transfer it over USB, and start the container.

---

## 3a. Register entry point and write `deploy_rig.py` with `--dry-run` first

Write `--dry-run` before the real deployment logic. This lets you iterate on SSH command generation and L4T-to-tag mapping on any machine — no ZED Box required.

**Harness — run before writing anything:**
```bash
uv run deploy-rig --dry-run --host user@192.168.55.1
```
Expect: `No such command 'deploy-rig'`. Red.

**Implementation — register the entry point in `scripts/pyproject.toml`:**
```toml
deploy-rig = "scripts.deploy_rig:main"
```

**Implementation — create `scripts/src/scripts/deploy_rig.py`:**

Implement `--dry-run` first: the flag makes the script print every shell command it would run, in order, without executing any of them. The full execution path (SSH, docker save, scp, docker load) is identical whether dry-run or not; only the subprocess calls are swapped for `print()`.

Runs on the user's host PC (not the Jetson). Uses `common.run_command.run_command` and `typer`, consistent with other scripts in the `scripts` package. Default host: `user@192.168.55.1`.

Flow:
1. **Pull** — `docker pull ghcr.io/outernet-foundation/placeframe/zed-capture:latest` on the host.
2. **Save** — `docker save -o /tmp/zed-capture.tar ghcr.io/.../zed-capture:latest`.
3. **Transfer** — `scp /tmp/zed-capture.tar {host}:/tmp/zed-capture.tar` and `scp zed/compose.rig.yml {host}:/tmp/compose.rig.yml`.
4. **Install** — `ssh {host} "docker load -i /tmp/zed-capture.tar && docker compose -f /tmp/compose.rig.yml up -d"`.
5. **Cleanup** — Delete `/tmp/zed-capture.tar` locally; `ssh {host} "rm /tmp/zed-capture.tar"`.

**Verify dry-run:**
```bash
uv run deploy-rig --dry-run --host user@192.168.55.1
```
Expect: each step prints the command that would be executed, in order. No connections made. Green without a ZED Box.

**Static analysis:**
```bash
uv run basedpyright
uv run ruff check scripts/
```
Expect: exit 0.

## 3b. Create `zed/compose.rig.yml`

Minimal compose for the ZED Box. No template substitution needed — single image tag.

```yaml
services:
  zed-capture:
    image: ghcr.io/outernet-foundation/placeframe/zed-capture:latest
    network_mode: host
    privileged: true
    devices:
      - /dev/bus/usb:/dev/bus/usb
    volumes:
      - captures:/root/captures
    restart: unless-stopped

volumes:
  captures:
```

## 3c. Delete `zed/install.py`

The systemd-based deploy is replaced entirely by `deploy-rig`. Delete `zed/install.py` and remove any comment referencing it from `zed/pyproject.toml`.

**Verify:**
```bash
uv run basedpyright
```
Expect: exit 0 (no dangling imports).

---

## Files to modify/create

| File | Action |
|---|---|
| `scripts/src/scripts/deploy_rig.py` | Create new |
| `scripts/pyproject.toml` | Add `deploy-rig` entry point |
| `zed/compose.rig.yml` | Create new |
| `zed/install.py` | Delete |

## Verification

- `uv run deploy-rig --dry-run --host user@192.168.55.1` prints the correct step sequence with no connections made
- `uv run deploy-rig --host user@192.168.55.1` completes on real hardware
- `docker ps` on the ZED Box shows the container running
- `curl http://192.168.55.1:9000/docs` returns the OpenAPI UI

## Done when

**Verifiable now (no special infra):**
- `uv run deploy-rig --dry-run` prints correct command sequence

**Requires ZED Box (verify manually later):**
- Full deploy completes

## Log

Clean implementation, no issues.

## Observations

- `zed/install.py` used `common.bash.bash` (not `common.run_command`) and `typer.run` instead of `typer.Typer()` — both are older patterns. The old file is now deleted so no action needed.
- `scripts/src/scripts/list_debug_targets.py` uses raw `subprocess.check_output` instead of `common.run_command`. Pre-existing, not introduced by this branch.
- `scripts/src/scripts/forward_unity_android_debug_port.py` uses `common.bash.bash_output` instead of `common.run_command`. Pre-existing.
