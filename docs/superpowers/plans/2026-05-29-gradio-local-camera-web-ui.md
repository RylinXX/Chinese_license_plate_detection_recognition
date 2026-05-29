# Gradio Local Camera Web UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a browser webcam test tab to the existing Gradio license plate recognition UI.

**Architecture:** Use Gradio's browser webcam source for capture and keep inference in the existing single-frame helper. Add a tiny `recognize_camera_frame` adapter so webcam behavior is testable without model weights, then use a Timer plus Start/Stop state for controlled polling.

**Tech Stack:** Python, Gradio webcam streaming, Pillow, OpenCV, pytest.

---

## File Structure

- Modify `web_app.py`: add `recognize_camera_frame` and a `Camera` tab.
- Modify `tests/test_web_app.py`: add focused camera adapter tests.

## Task 1: Camera Adapter

**Files:**
- Modify: `tests/test_web_app.py`
- Modify: `web_app.py`

- [ ] **Step 1: Write failing tests**

Add tests for:

- `recognize_camera_frame(None, models, 640)` returns `(None, [], "Waiting for camera frame.")`.
- `recognize_camera_frame(image, models, 640, is_running=False)` returns `(None, [], "Camera recognition stopped.")`.
- `recognize_camera_frame(image, models, 640, mirror_correction=True)` flips the frame before detection.
- `recognize_camera_frame(image, models, 1280, detector=fake, drawer=fake)` passes `1280` into the detector and returns the annotated RGB frame.

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_web_app.py -v
```

Expected: import failure because `recognize_camera_frame` does not exist.

- [ ] **Step 3: Implement adapter**

Add:

```python
def recognize_camera_frame(
    image: Image.Image | None,
    models: ModelBundle,
    img_size: Any,
    mirror_correction: bool = False,
    is_running: bool = True,
    detector: Detector | None = None,
    drawer: Drawer | None = None,
) -> tuple[np.ndarray | None, list[dict[str, str]], str]:
    if not is_running:
        return None, [], "Camera recognition stopped."
    if image is None:
        return None, [], "Waiting for camera frame."
    if mirror_correction:
        image = ImageOps.mirror(image)
    return recognize_image(image, models, img_size=img_size, detector=detector, drawer=drawer)
```

- [ ] **Step 4: Run tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_web_app.py -v
```

Expected: all tests pass.

## Task 2: Camera Tab UI

**Files:**
- Modify: `web_app.py`

- [ ] **Step 1: Add Gradio camera tab**

Add a `Camera` tab in `build_interface`:

- `gr.Image(sources="webcam", streaming=True, type="pil", label="Camera")`
- `gr.Radio([640, 1280], value=640, label="Recognition size")`
- `gr.Checkbox(value=True, label="Mirror correction")`
- `gr.State(False)` for running state
- `gr.Timer(0.7, active=True)` for polling
- `Start Recognition` and `Stop Recognition` buttons
- `gr.Image(type="numpy", label="Annotated camera frame")`
- `gr.JSON(label="Camera recognition details")`
- `gr.Textbox(label="Camera status", interactive=False)`
- Bind `timer.tick(...)` to `recognize_camera_frame` through a local `predict_camera` wrapper.
- Bind the start button to set running state true.
- Bind the stop button to set running state false.

- [ ] **Step 2: Run tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_web_app.py -v
```

Expected: all tests pass.

## Task 3: Verification

**Files:**
- No planned file changes.

- [ ] **Step 1: CLI help**

Run:

```powershell
.\.venv\Scripts\python.exe web_app.py --help
```

Expected: help prints successfully.

- [ ] **Step 2: Restart app and HTTP check**

Run the app on `127.0.0.1:7860`, then request `http://127.0.0.1:7860`.

Expected: HTTP 200.

- [ ] **Step 3: Browser smoke test**

Use Playwright to confirm these labels render:

- `Camera`
- `Annotated camera frame`
- `Camera recognition details`
- `Camera status`
- `640`
- `1280`

Expected: all labels are visible or present in page text.
