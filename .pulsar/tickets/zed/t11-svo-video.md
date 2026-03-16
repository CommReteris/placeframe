---
id: T11
title: SVO video capture refactor
status: in-progress
depends_on: [T10]
---

# T11: SVO video capture refactor

## Goal

Replace per-frame JPEG extraction with SVO hardware-encoded video via the Jetson's NVENC encoder, freeing CPU for positional tracking.

## Context

Currently `_capture_frame` in `zed.py` retrieves and writes four images (left/right camera JPEGs) per frame during capture. This is CPU-intensive. The ZED SDK can record directly to SVO format using hardware H.265 encoding, with frames extracted at stop time to preserve backward compatibility with the downstream `reconstructor` service.

All changes are within `zed/`. There is no test runner; static analysis is the feedback loop.

---

## 2a. Establish static analysis baseline

Run both tools before touching any code. Any pre-existing failures must be fixed first so the baseline is clean — subsequent red states are unambiguously caused by changes made in 2b–2d.

```bash
uv run basedpyright
uv run ruff check zed/
```

Both must exit 0 before proceeding. Run after every subsequent step.

## 2b. Add `enable_recording` / `disable_recording` to `zed_wrapper.py`

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

## 2c. Refactor `zed.py` — add SVO recording, strip JPEG writes from capture loop

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

## 2d. Add `_extract_frames_from_svo` and update `_stop`

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

## 2e. Verify `zed_stub.py`

No signature changes needed. Confirm `start_capture(capture_interval: float)` and `stop_capture()` still match. No code change expected here.

---

## Files to modify

| File | Action |
|---|---|
| `zed/src/zed/zed.py` | SVO recording in `_start`, strip image writes from `_capture_frame`, add `_extract_frames_from_svo` to `_stop` |
| `zed/src/zed/zed_wrapper.py` | Add `enable_recording`, `disable_recording` |
| `zed/src/zed/zed_stub.py` | Verify only |

## Final output structure

Same as before, plus `video.svo2`:
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

## Verification

`uv run basedpyright` and `uv run ruff check zed/` pass after every step. On hardware: `video.svo2` appears in the capture directory, `frames.csv` is populated, and `camera0/`/`camera1/` JPEGs are written after stop.

## Done when

**Verifiable now (no special infra):**
- `uv run basedpyright` and `uv run ruff check zed/` pass

**Requires ZED hardware (verify manually later):**
- SVO recording + extraction works
