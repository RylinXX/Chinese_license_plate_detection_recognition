# Gradio Batch Video Web UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the existing Gradio web UI with batch image recognition, video recognition, and a 640/1280 recognition size selector.

**Architecture:** Keep `web_app.py` as the web adapter around existing model functions. Add helper functions that are easy to test without weights: image size normalization, batch aggregation, video output path creation, and video processing with injectable detector/drawer hooks.

**Tech Stack:** Python, Gradio, OpenCV, Pillow, PyTorch, pytest.

---

## File Structure

- Modify `web_app.py`: add size selection, batch image function, video function, and tabbed Gradio UI.
- Modify `tests/test_web_app.py`: add focused helper tests without loading model weights.

## Task 1: Recognition Size Tests and Implementation

**Files:**
- Modify: `tests/test_web_app.py`
- Modify: `web_app.py`

- [ ] **Step 1: Write failing tests**

Add tests that import and exercise `normalize_img_size`, and update the existing `recognize_image` adapter test to pass `img_size=1280` and assert the fake detector receives `1280`.

- [ ] **Step 2: Run tests to verify failure**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_web_app.py -v`

Expected: import or assertion failure because `normalize_img_size` and the override do not exist yet.

- [ ] **Step 3: Implement minimal code**

Add `normalize_img_size(value)` returning `640` or `1280`, and add optional `img_size` to `recognize_image`; use `normalize_img_size(img_size or models.img_size)` for detector calls.

- [ ] **Step 4: Run tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_web_app.py -v`

Expected: all tests pass.

## Task 2: Batch Image Tests and Implementation

**Files:**
- Modify: `tests/test_web_app.py`
- Modify: `web_app.py`

- [ ] **Step 1: Write failing tests**

Add tests for:

- Empty batch returns `([], [], "No images were provided.")`.
- Two temporary image files produce two gallery entries and two summary items.

- [ ] **Step 2: Run tests to verify failure**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_web_app.py -v`

Expected: failure because `recognize_batch_images` does not exist.

- [ ] **Step 3: Implement minimal code**

Add `UploadedFile` path extraction helper and `recognize_batch_images(files, models, img_size, detector=None, drawer=None)`.

- [ ] **Step 4: Run tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_web_app.py -v`

Expected: all tests pass.

## Task 3: Video Tests and Implementation

**Files:**
- Modify: `tests/test_web_app.py`
- Modify: `web_app.py`

- [ ] **Step 1: Write failing tests**

Add tests for:

- `make_output_video_path(tmp_path / "in.mp4")` returns an `.mp4` path with `annotated` in the name.
- `recognize_video(None, models, 640)` returns `(None, {"status": "No video was provided."}, "No video was provided.")`.
- An unreadable path returns a readable failure status.

- [ ] **Step 2: Run tests to verify failure**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_web_app.py -v`

Expected: failure because video helpers do not exist.

- [ ] **Step 3: Implement minimal code**

Add `make_output_video_path` and `recognize_video`. Use OpenCV `VideoCapture`, preserve input FPS/size where available, write annotated frames with `mp4v`, and aggregate detected rows per frame.

- [ ] **Step 4: Run tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_web_app.py -v`

Expected: all tests pass.

## Task 4: Tabbed Gradio UI

**Files:**
- Modify: `web_app.py`

- [ ] **Step 1: Update UI**

Change `build_interface` to use tabs:

- `Single Image`: image input, 640/1280 radio, annotated image, JSON, status.
- `Batch Images`: file upload with multiple files, 640/1280 radio, gallery, JSON, status.
- `Video`: video upload, 640/1280 radio, output video, JSON, status.

- [ ] **Step 2: Run tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_web_app.py -v`

Expected: all tests pass.

## Task 5: Verification

**Files:**
- No planned file changes.

- [ ] **Step 1: Run unit tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_web_app.py -v`

Expected: all tests pass.

- [ ] **Step 2: Check CLI help**

Run: `.\.venv\Scripts\python.exe web_app.py --help`

Expected: CLI help prints successfully.

- [ ] **Step 3: Restart local app and check HTTP**

Run the app on `127.0.0.1:7860`, then request `http://127.0.0.1:7860`.

Expected: HTTP 200.

- [ ] **Step 4: Browser smoke test**

Use Playwright to verify the tabs and `640`/`1280` choices render.

Expected: Single Image, Batch Images, Video, 640, and 1280 are visible.
