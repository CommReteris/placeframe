# T13: ZED hardware documentation

## Goal

Rewrite `zed/README.md` with hardware BOM, cable connections, and one-command deployment workflow.

## Context

The current `zed/README.md` is a developer-facing JetPack setup guide. It should be replaced with a user-facing hardware quickstart now that `deploy-rig` handles all the deployment complexity.

---

## Implementation

Replace the current README with:

1. **Hardware BOM**
   - ZED Box Mini (or ZED Box)
   - ZED X camera
   - FAKRA cable (ZED X to ZED Box)
   - **12V Buck/Boost Regulator** wired to the green terminal block — required to avoid frying the board with laptop battery voltage

2. **Cable connections**
   - 12V power → green terminal block
   - Micro-USB OTG port → host laptop

3. **One-command deployment**
   ```bash
   uv run deploy-rig --host user@192.168.55.1
   ```

4. **After deployment**
   - Unplug Micro-USB, plug in Android phone
   - Unity app connects to `192.168.55.1:9000`

Move existing developer notes (building PyZED wheel, systemd setup) to a collapsible `<details>` section or `zed/DEVELOPER.md`.

## Files to modify

| File | Action |
|---|---|
| `zed/README.md` | Rewrite |

## Depends on

T12 (documents the deploy-rig workflow).

## Done when

- `zed/README.md` rewritten with BOM, cable connections, and deploy command
