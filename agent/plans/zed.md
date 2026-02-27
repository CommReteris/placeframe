# Plan: ZED Box Capture Rig Refactors

## Context

Four-phase plan to modernise the ZED camera capture rig:
1. **Self-healing CI/CD** — auto-build new JetPack-specific Docker images whenever Stereolabs releases a new base image, using QEMU to spoof aarch64 during the build so `get_python_api.py` downloads the correct PyZED wheel automatically.
2. **SVO video** — replace per-frame JPEG extraction with the Jetson's NVENC hardware encoder via `pyzed.sl.RecordingParameters`, freeing CPU for positional tracking.
3. **Zero-internet deploy script** — a host-side Python script that bridges the gap between the user's laptop (internet) and the ZED Box (no internet) over the USB gadget link at `192.168.55.1`.
4. **README hardware docs** — document the BOM and one-command workflow.

---

## Phase 1 — Self-Healing CI/CD Pipeline

### 1a. One-time local environment setup

Confirm QEMU binfmt support and a multi-platform Buildx builder are available. These are prerequisites for all build tests in this phase.

```bash
docker run --privileged --rm tonistiigi/binfmt --install all
docker buildx create --name multiplatform --driver docker-container --use
docker buildx inspect --bootstrap
```

### 1b. `renovate.json`

**Harness — run before writing the file:**
```bash
docker run --rm \
  -v "$(pwd)/renovate.json":/usr/src/app/renovate.json \
  renovate/renovate renovate-config-validator /usr/src/app/renovate.json
```
Expect: failure (file doesn't exist). Red.

**Implementation — create `/renovate.json`:**

Create a Renovate configuration that watches the `stereolabs/zed` Docker Hub repository so that when Stereolabs drops a new JetPack base image, Renovate opens a PR updating the `ZED_BASE_IMAGE` ARG strings in the bake file.

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"],
  "docker": {
    "enabled": true
  },
  "packageRules": [
    {
      "matchDatasources": ["docker"],
      "matchPackageNames": ["stereolabs/zed"],
      "groupName": "ZED Base Image"
    }
  ]
}
```

**Verify:**
```bash
docker run --rm \
  -v "$(pwd)/renovate.json":/usr/src/app/renovate.json \
  renovate/renovate renovate-config-validator /usr/src/app/renovate.json
```
Expect: exit 0. Green.

### 1c. `compose.bake.yml` ZED targets + `docker/zed-capture/Dockerfile`

Add the bake targets before writing the Dockerfile so `--print` validates YAML resolution immediately, and the failing `--load` then drives writing the Dockerfile.

**Harness — validate bake YAML without pulling any images:**
```bash
docker buildx bake -f compose.bake.yml zed-capture-jp62 --print
```
Expect: failure (target doesn't exist). Red.

**Implementation — add ZED targets to `compose.bake.yml`:**

Add two new services following the existing `reconstructor-cuda` / `reconstructor-rocm` pattern:

```yaml
  zed-capture-jp62:
    build:
      context: .
      dockerfile: docker/zed-capture/Dockerfile
      args:
        <<: *base-args
        ZED_BASE_IMAGE: "stereolabs/zed:5.0-runtime-jetson-jp6.2"
      tags: [ "ghcr.io/outernet-foundation/placeframe/zed-capture:jp6.2" ]
      platforms: ["linux/arm64"]

  zed-capture-jp51:
    build:
      context: .
      dockerfile: docker/zed-capture/Dockerfile
      args:
        <<: *base-args
        ZED_BASE_IMAGE: "stereolabs/zed:4.2-runtime-jetson-jp5.1.2"
      tags: [ "ghcr.io/outernet-foundation/placeframe/zed-capture:jp5.1" ]
      platforms: ["linux/arm64"]
```

**Verify YAML resolution:**
```bash
docker buildx bake -f compose.bake.yml zed-capture-jp62 --print
```
Expect: resolved JSON printed, exit 0. Green for YAML. The Dockerfile is still missing, so proceed.

**Build harness — drive writing the Dockerfile:**
```bash
docker buildx bake -f compose.bake.yml zed-capture-jp62 --load
```
Expect: failure (Dockerfile missing). Red.

**Implementation — create `docker/zed-capture/Dockerfile`:**

Accepts `ZED_BASE_IMAGE` as a build ARG, installs `uv`, runs `get_python_api.py` (QEMU intercepts `platform.machine()` so it fetches the aarch64 wheel even on x86), copies the wheel into the vendored location, and installs the `zed` package via `uv sync`.

```dockerfile
ARG ZED_BASE_IMAGE=stereolabs/zed:5.0-runtime-jetson-jp6.2
FROM ${ZED_BASE_IMAGE}

ARG UV_BASE_DIGEST
FROM ${UV_BASE_DIGEST:-ghcr.io/astral-sh/uv:python3.13-bookworm-slim} AS uv

FROM ${ZED_BASE_IMAGE}

# Install uv
COPY --from=uv /uv /uvx /usr/local/bin/

# Download the correct PyZED wheel for this JetPack base.
# QEMU intercepts platform.machine() so get_python_api.py fetches the aarch64 wheel
# even when building on x86 GitHub Actions runners.
RUN python3 /usr/local/zed/get_python_api.py --target /tmp/pyzed_wheel
# Copy wheel into the vendored location so pyproject.toml path sources still resolve
RUN cp /tmp/pyzed_wheel/pyzed-*.whl zed/third-party/pyzed/

# Copy monorepo workspace files needed by the zed package
COPY pyproject.toml uv.lock ./
COPY packages/python/common ./packages/python/common
COPY packages/python/core ./packages/python/core
COPY zed ./zed

ENV UV_NO_CACHE=1
RUN uv sync --package zed --frozen --no-dev

CMD ["uv", "run", "--package", "zed", "--no-sync", \
     "uvicorn", "src.main:app", \
     "--app-dir", "zed", \
     "--host", "0.0.0.0", "--port", "9000"]
```

**Verify — build should now succeed:**
```bash
docker buildx bake -f compose.bake.yml zed-capture-jp62 --load
```
Expect: exit 0, image present in local daemon. Green.

### 1d. Renovate detection round-trip

With `renovate.json` and the `compose.bake.yml` ZED targets both written, verify Renovate detects the `stereolabs/zed` references and would open a PR on a version bump.

**B1 — dry-run against real Docker Hub:**
```bash
docker run --rm \
  -e LOG_LEVEL=debug \
  -v "$(pwd)":/usr/src/app \
  renovate/renovate \
    --platform=local \
    --dry-run=full \
    --config-file=/usr/src/app/renovate.json \
    .
```
Expect: output includes `"ZED Base Image"` group and references to the `stereolabs/zed` image. If the pinned tag is already the latest on Docker Hub, Renovate correctly reports "nothing to update" — this is not a failure; it means the config is wired correctly but there's nothing to bump right now. Proceed to B2 only in that case.

**B2 — local registry with fake newer tag (only needed if B1 reports "nothing to update"):**

```bash
# Start local registry
docker run -d -p 5000:5000 --name fake-registry registry:2

# Use alpine as a stand-in for the 7 GB ZED base
docker pull alpine:latest
docker tag alpine:latest localhost:5000/stereolabs/zed:5.0-runtime-jetson-jp6.2
docker push localhost:5000/stereolabs/zed:5.0-runtime-jetson-jp6.2

# The "new" version Renovate should detect
docker tag alpine:latest localhost:5000/stereolabs/zed:5.1-runtime-jetson-jp6.2
docker push localhost:5000/stereolabs/zed:5.1-runtime-jetson-jp6.2
```

Temporarily add `"registryUrls": ["http://localhost:5000"]` to the `packageRules` entry in `renovate.json`, and change both `ZED_BASE_IMAGE` values in `compose.bake.yml` to `localhost:5000/stereolabs/zed:5.0-runtime-jetson-jp6.2`. **Revert both before merging.**

```bash
docker run --rm \
  -e LOG_LEVEL=debug \
  --network=host \
  -v "$(pwd)":/usr/src/app \
  renovate/renovate \
    --platform=local \
    --dry-run=full \
    --config-file=/usr/src/app/renovate.json \
    .
```
Expect: Renovate reports a pending PR bumping `ZED_BASE_IMAGE` to `5.1-runtime-jetson-jp6.2`.

**Cleanup:**
```bash
docker stop fake-registry && docker rm fake-registry
# Revert renovate.json and compose.bake.yml patches
```

### 1e. `.github/workflows/build.yml`

**Harness — confirm `act` is installed and can parse the workflow:**
```bash
act push -W .github/workflows/build.yml --list
```
Expect: lists the `build-and-lock` job steps. If `act` isn't installed, that's the red state — install via `brew install act` / `winget install nektos.act`.

**Implementation — add ZED build step** after the existing ROCm build:

```yaml
      - name: Build ZED Capture Images
        run: |
          echo "::group::ZED Capture Images"
          docker buildx bake -f compose.bake.yml zed-capture-jp62 zed-capture-jp51 --push
          echo "::endgroup::"
```

This step does not need the free-disk-space workaround (no Torch layers).

**Verify:**
```bash
act push -W .github/workflows/build.yml \
  --secret GITHUB_TOKEN="$(gh auth token)" \
  -P ubuntu-latest=catthehacker/ubuntu:act-latest
```
Store secrets in a `.secrets` file (add to `.gitignore`) and pass with `--secret-file .secrets` if preferred. Expect: all steps including "Build ZED Capture Images" exit 0.

---

## Phase 2 — Refactor `zed.py` for SVO Video

All changes are within `zed/`. There is no test runner; static analysis is the feedback loop.

### 2a. Establish static analysis baseline

Run both tools before touching any code. Any pre-existing failures must be fixed first so the baseline is clean — subsequent red states are unambiguously caused by changes made in 2b–2d.

```bash
uv run basedpyright
uv run ruff check zed/
```

Both must exit 0 before proceeding. Run after every subsequent step.

### 2b. Add `enable_recording` / `disable_recording` to `zed_wrapper.py`

File: `zed/src/zed/zed_wrapper.py`

Add two new wrapper functions after `disable_positional_tracking`:

```python
def enable_recording(cam: sl.Camera, params: sl.RecordingParameters) -> None:
    error = cam.enable_recording(params)
    if error != sl.ERROR_CODE.SUCCESS:
        raise Exception(f"ZED Enable Recording Error: {error}")

def disable_recording(cam: sl.Camera) -> None:
    cam.disable_recording()
```

**Verify:**
```bash
uv run basedpyright
uv run ruff check zed/
```
Expect: exit 0. Type errors here indicate an import or signature issue in the pyzed stubs.

### 2c. Refactor `zed.py` — add SVO recording, strip JPEG writes from capture loop

File: `zed/src/zed/zed.py`

**Add to imports:**
- `RecordingParameters, SVO_COMPRESSION_MODE, TIME_REFERENCE` from `pyzed.sl`
- `enable_recording, disable_recording` from `.zed_wrapper`

**In `__init__`:** Remove `self._image_buffer_matrix = Mat()` (line 89). No longer allocated during capture — only used at stop-time extraction.

**In `_start` (lines 180–286):**
- Replace the two `_camera0_directory().mkdir()` / `_camera1_directory().mkdir()` calls with `self._rig_directory().mkdir(parents=True, exist_ok=True)` (JPEGs are created at stop time, not start time).
- After `open_camera` and the sharpness check, add SVO recording initialisation **before** `_meter_and_lock`:
  ```python
  recording_params = RecordingParameters()
  recording_params.video_filename = str(self._rig_directory() / "video.svo2")
  recording_params.compression_mode = SVO_COMPRESSION_MODE.H265
  enable_recording(self._camera, recording_params)
  ```

**In `_capture_frame` (lines 293–312):**
- Remove the four image retrieval/write lines (lines 309–312). Keep only `grab()`, `update_pose()`, and the CSV write. The SDK silently writes every `grab()` call to the SVO via NVENC.

**Verify:**
```bash
uv run basedpyright
uv run ruff check zed/
```

### 2d. Add `_extract_frames_from_svo` and update `_stop`

File: `zed/src/zed/zed.py`

`_stop` sequence: `disable_recording` → `disable_positional_tracking` → `close_camera` → `_extract_frames_from_svo`.

`_extract_frames_from_svo` re-opens the SVO in playback mode and extracts every frame to the existing `camera0/` / `camera1/` JPEG directory structure, preserving full backward compatibility with the downstream `reconstructor` service:

```python
def _extract_frames_from_svo(self):
    print("Extracting frames from SVO")
    self._camera0_directory().mkdir(parents=True, exist_ok=True)
    self._camera1_directory().mkdir(parents=True, exist_ok=True)

    init = InitParameters()
    init.set_from_svo_file(str(self._rig_directory() / "video.svo2"))
    init.svo_real_time_mode = False
    open_camera(self._camera, init)

    svo_image = Mat()
    while True:
        try:
            grab(self._camera)
        except Exception:
            break  # end of SVO

        timestamp = int(self._camera.get_timestamp(TIME_REFERENCE.IMAGE).get_milliseconds())
        retrieve_image(self._camera, svo_image, VIEW.LEFT)
        self._write_jpeg(svo_image, self._camera0_directory() / f"{timestamp}.jpg")
        retrieve_image(self._camera, svo_image, VIEW.RIGHT)
        self._write_jpeg(svo_image, self._camera1_directory() / f"{timestamp}.jpg")

    close_camera(self._camera)
    self._camera = Camera()  # re-init for next session
```

`Mat`, `VIEW`, `retrieve_image`, `get_data`, `_write_jpeg`, `_camera0_directory`, `_camera1_directory` are all **kept** (needed for extraction). `PIL` import is kept. `pyproject.toml` is unchanged.

**Verify:**
```bash
uv run basedpyright
uv run ruff check zed/
```

**Final output structure** (same as before, plus `video.svo2`):
```
<capture_id>/
├── rig0/
│   ├── video.svo2        ← hardware-encoded H.265, all frames at camera FPS
│   ├── camera0/          ← extracted LEFT JPEGs: {timestamp_ms}.jpg
│   ├── camera1/          ← extracted RIGHT JPEGs: {timestamp_ms}.jpg
│   └── frames.csv
├── manifest.json
└── metered_values.json
```

### 2e. Verify `zed_stub.py`

No signature changes needed. Confirm `start_capture(capture_interval: float)` and `stop_capture()` still match. No code change expected here.

---

## Phase 3 — Zero-Internet Deployment Script

### 3a. Register entry point and write `deploy_rig.py` with `--dry-run` first

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
1. **Probe** — `ssh {host} "cat /etc/nv_tegra_release"` — detect L4T major revision.
2. **Map** — Parse L4T revision to image tag (`R36.*` → `jp6.2`, `R35.*` → `jp5.1`).
3. **Pull** — `docker pull ghcr.io/outernet-foundation/placeframe/zed-capture:{tag}` on the host.
4. **Save** — `docker save -o /tmp/zed-capture.tar ghcr.io/.../zed-capture:{tag}`.
5. **Render compose** — Read `zed/compose.rig.yml`, substitute the image tag, write to a temp file.
6. **Transfer** — `scp /tmp/zed-capture.tar {host}:/tmp/zed-capture.tar` and `scp {compose_tmp} {host}:/tmp/compose.rig.yml`.
7. **Install** — `ssh {host} "docker load -i /tmp/zed-capture.tar && docker compose -f /tmp/compose.rig.yml up -d"`.
8. **Cleanup** — Delete `/tmp/zed-capture.tar` locally; `ssh {host} "rm /tmp/zed-capture.tar"`.

**Verify dry-run:**
```bash
uv run deploy-rig --dry-run --host user@192.168.55.1
```
Expect: each step prints the command that would be executed, in order. No connections made. Confirm the L4T-to-tag mapping logic is correct by reading the printed output. Green without a ZED Box.

**Static analysis:**
```bash
uv run basedpyright
uv run ruff check scripts/
```
Expect: exit 0.

### 3b. Create `zed/compose.rig.yml`

Minimal compose for the ZED Box. Image tag is a template placeholder substituted by `deploy_rig.py` before scp. No separate test needed — the file is validated implicitly when `deploy_rig.py --dry-run` reads and renders it.

```yaml
services:
  zed-capture:
    image: ghcr.io/outernet-foundation/placeframe/zed-capture:{TAG}
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

Re-run `uv run deploy-rig --dry-run --host user@192.168.55.1` after creating this file to confirm the rendered compose output looks correct.

### 3c. Delete `zed/install.py`

The systemd-based deploy is replaced entirely by `deploy-rig`. Delete `zed/install.py` and remove any comment referencing it from `zed/pyproject.toml`.

**Verify:**
```bash
uv run basedpyright
```
Expect: exit 0 (no dangling imports).

---

## Phase 4 — README Hardware Documentation

### 4a. Rewrite `zed/README.md`

Replace the current developer-facing JetPack setup guide with a user-facing hardware quickstart:

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

---

## Critical Files

| File | Action |
|---|---|
| `zed/src/zed/zed.py` | Modify — SVO recording in `_start`, strip image writes from `_capture_frame`, add `_extract_frames_from_svo` to `_stop` |
| `zed/src/zed/zed_wrapper.py` | Modify — add `enable_recording`, `disable_recording` |
| `zed/src/zed/zed_stub.py` | Verify only |
| `docker/zed-capture/Dockerfile` | Create new |
| `compose.bake.yml` | Modify — add `zed-capture-jp62` / `zed-capture-jp51` targets |
| `.github/workflows/build.yml` | Modify — add ZED capture build step |
| `renovate.json` | Create new |
| `scripts/src/scripts/deploy_rig.py` | Create new |
| `scripts/pyproject.toml` | Modify — add `deploy-rig` entry point |
| `zed/compose.rig.yml` | Create new |
| `zed/install.py` | Delete |
| `zed/README.md` | Rewrite |

## Decisions

- **SVO + downstream pipeline:** `_extract_frames_from_svo` runs at stop time so the download tarball retains the existing JPEG directory structure; the `reconstructor` service needs no changes.
- **`install.py` fate:** Deleted — Docker-based `deploy-rig` is the only deployment path.
- **`deploy_rig.py` entry point:** `uv run deploy-rig` registered in `scripts/pyproject.toml`.
- **`compose.rig.yml` tag substitution:** Python string substitution in the deploy script before scp.
- **TDD gate per phase:** Phase 1 — `bake --print` then `bake --load` then Renovate dry-run; Phase 2 — `basedpyright` + `ruff check` established as baseline before any edits, run after each step; Phase 3 — `--dry-run` flag written and passing before any real deployment logic.

## Verification

- **Phase 1:** `docker buildx bake -f compose.bake.yml zed-capture-jp62 --print` exits 0; `renovate-config-validator renovate.json` exits 0; Renovate B1 dry-run output includes `"ZED Base Image"` group; Renovate B2 dry-run reports a pending `5.1` bump; `act push` completes "Build ZED Capture Images" without error; push to `main` builds and pushes both tags to GHCR.
- **Phase 2:** `uv run basedpyright` and `uv run ruff check zed/` pass after every step. On hardware: `video.svo2` appears in the capture directory, `frames.csv` is populated, and `camera0/`/`camera1/` JPEGs are written after stop.
- **Phase 3:** `uv run deploy-rig --dry-run --host user@192.168.55.1` prints the correct step sequence with no connections made; `uv run deploy-rig --host user@192.168.55.1` completes on real hardware; `docker ps` on the ZED Box shows the container running; `curl http://192.168.55.1:9000/docs` returns the OpenAPI UI.
