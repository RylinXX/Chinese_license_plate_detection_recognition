# Gradio Image Web UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Gradio web interface that lets a user upload one image and view license plate recognition results.

**Architecture:** Add one focused root-level `web_app.py` module. Keep model inference in the existing `detect_plate.py` and `plate_recognition` functions; `web_app.py` only adapts uploaded images, formats result data, builds the Gradio UI, and launches it.

**Tech Stack:** Python, Gradio, OpenCV, Pillow, PyTorch, pytest.

---

## File Structure

- Create `web_app.py`: Gradio UI, CLI args, model startup, image conversion, inference adapter, result formatting.
- Create `tests/test_web_app.py`: helper tests that do not load model weights.
- Modify `requirements.txt`: add `gradio` and `pytest` so the UI and tests are declared dependencies.

## Task 1: Helper Tests

**Files:**
- Create: `tests/test_web_app.py`
- Create in Task 2: `web_app.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_web_app.py`:

```python
import numpy as np
from PIL import Image

from web_app import format_results, pil_to_bgr


def test_format_results_reports_no_plate_for_empty_result():
    rows, message = format_results([])

    assert rows == []
    assert message == "No license plate detected."


def test_format_results_extracts_plate_fields():
    rows, message = format_results(
        [
            {
                "plate_no": "TEST123",
                "plate_color": "blue",
                "detect_conf": 0.91,
                "rec_conf": 0.82,
                "plate_type": 0,
            }
        ]
    )

    assert message == "Detected 1 license plate."
    assert rows == [
        {
            "plate": "TEST123",
            "color": "blue",
            "detect_confidence": "0.910",
            "recognition_confidence": "0.820",
            "plate_type": "single",
        }
    ]


def test_format_results_averages_character_confidences():
    rows, message = format_results(
        [
            {
                "plate_no": "TEST456",
                "plate_color": "",
                "detect_conf": 0.5,
                "rec_conf": [0.7, 0.8, 0.9],
                "plate_type": 1,
            }
        ]
    )

    assert message == "Detected 1 license plate."
    assert rows[0]["recognition_confidence"] == "0.800"
    assert rows[0]["plate_type"] == "double"


def test_pil_to_bgr_converts_rgb_image_to_bgr_array():
    image = Image.new("RGB", (2, 1), color=(10, 20, 30))

    result = pil_to_bgr(image)

    assert result.shape == (1, 2, 3)
    assert result.dtype == np.uint8
    assert result[0, 0].tolist() == [30, 20, 10]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_web_app.py -v
```

Expected: FAIL during import because `web_app` does not exist yet.

- [ ] **Step 3: Commit is skipped for red state**

Do not commit failing tests alone.

## Task 2: Minimal Helper Implementation

**Files:**
- Create: `web_app.py`
- Test: `tests/test_web_app.py`

- [ ] **Step 1: Implement the helper functions only**

Create the top part of `web_app.py` with:

```python
from __future__ import annotations

from typing import Any

import cv2
import numpy as np
from PIL import Image


def pil_to_bgr(image: Image.Image) -> np.ndarray:
    if image is None:
        raise ValueError("No image was provided.")
    rgb_image = image.convert("RGB")
    rgb_array = np.asarray(rgb_image, dtype=np.uint8)
    return cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)


def _format_confidence(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, np.ndarray)):
        if len(value) == 0:
            return ""
        value = float(np.mean(value))
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return ""


def _plate_type_label(value: Any) -> str:
    try:
        return "double" if int(value) else "single"
    except (TypeError, ValueError):
        return ""


def format_results(results: list[dict[str, Any]]) -> tuple[list[dict[str, str]], str]:
    if not results:
        return [], "No license plate detected."

    rows = []
    for result in results:
        rows.append(
            {
                "plate": str(result.get("plate_no", "")),
                "color": str(result.get("plate_color", "")),
                "detect_confidence": _format_confidence(result.get("detect_conf")),
                "recognition_confidence": _format_confidence(result.get("rec_conf")),
                "plate_type": _plate_type_label(result.get("plate_type")),
            }
        )

    noun = "license plate" if len(rows) == 1 else "license plates"
    return rows, f"Detected {len(rows)} {noun}."
```

- [ ] **Step 2: Run tests to verify helper implementation passes**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_web_app.py -v
```

Expected: 4 passed.

- [ ] **Step 3: Commit helper layer**

Run:

```powershell
git add web_app.py tests/test_web_app.py
git commit -m "Add Gradio web UI helpers"
```

## Task 3: Recognition Adapter and Gradio UI

**Files:**
- Modify: `web_app.py`

- [ ] **Step 1: Extend `web_app.py` with model loading and prediction**

Add imports and functions below the helper functions:

```python
import argparse
from dataclasses import dataclass
from pathlib import Path

import gradio as gr
import torch

from detect_plate import detect_Recognition_plate, draw_result, load_model
from plate_recognition.plate_rec import init_model


@dataclass
class ModelBundle:
    detect_model: Any
    rec_model: Any
    device: torch.device
    img_size: int
    is_color: bool


def load_models(
    detect_model_path: str,
    rec_model_path: str,
    img_size: int,
    is_color: bool,
    force_cpu: bool,
) -> ModelBundle:
    device = torch.device("cpu" if force_cpu or not torch.cuda.is_available() else "cuda")
    detect_model = load_model(detect_model_path, device)
    rec_model = init_model(device, rec_model_path, is_color=is_color)
    return ModelBundle(
        detect_model=detect_model,
        rec_model=rec_model,
        device=device,
        img_size=img_size,
        is_color=is_color,
    )


def recognize_image(image: Image.Image, models: ModelBundle) -> tuple[np.ndarray | None, list[dict[str, str]], str]:
    try:
        bgr_image = pil_to_bgr(image)
        results = detect_Recognition_plate(
            models.detect_model,
            bgr_image,
            models.device,
            models.rec_model,
            models.img_size,
            is_color=models.is_color,
        )
        annotated_bgr = draw_result(bgr_image.copy(), results, is_color=models.is_color)
        rows, message = format_results(results)
        annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
        return annotated_rgb, rows, message
    except Exception as exc:
        return None, [], f"Recognition failed: {exc}"
```

- [ ] **Step 2: Add UI construction and CLI launch**

Add this code at the bottom of `web_app.py`:

```python
def build_interface(models: ModelBundle) -> gr.Blocks:
    def predict(image: Image.Image) -> tuple[np.ndarray | None, list[dict[str, str]], str]:
        return recognize_image(image, models)

    with gr.Blocks(title="License Plate Recognition") as demo:
        gr.Markdown("# License Plate Recognition")
        gr.Markdown("Upload an image and run recognition locally.")

        with gr.Row():
            with gr.Column(scale=1):
                image_input = gr.Image(type="pil", label="Input image")
                recognize_button = gr.Button("Recognize", variant="primary")
            with gr.Column(scale=1):
                image_output = gr.Image(type="numpy", label="Annotated result")

        result_table = gr.Dataframe(
            headers=[
                "plate",
                "color",
                "detect_confidence",
                "recognition_confidence",
                "plate_type",
            ],
            datatype=["str", "str", "str", "str", "str"],
            label="Recognition details",
        )
        status_output = gr.Textbox(label="Status", interactive=False)

        recognize_button.click(
            fn=predict,
            inputs=image_input,
            outputs=[image_output, result_table, status_output],
        )

    return demo


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Gradio image recognition UI.")
    parser.add_argument("--detect_model", default="weights/plate_detect.pt")
    parser.add_argument("--rec_model", default="weights/plate_rec_color.pth")
    parser.add_argument("--img_size", type=int, default=640)
    parser.add_argument("--is_color", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--cpu", action="store_true", help="Force CPU inference.")
    parser.add_argument("--server_name", default="127.0.0.1")
    parser.add_argument("--server_port", type=int, default=7860)
    return parser.parse_args()


def validate_model_paths(detect_model_path: str, rec_model_path: str) -> None:
    missing = [path for path in [detect_model_path, rec_model_path] if not Path(path).exists()]
    if missing:
        raise FileNotFoundError("Missing model file(s): " + ", ".join(missing))


def main() -> None:
    args = parse_args()
    validate_model_paths(args.detect_model, args.rec_model)
    models = load_models(
        detect_model_path=args.detect_model,
        rec_model_path=args.rec_model,
        img_size=args.img_size,
        is_color=args.is_color,
        force_cpu=args.cpu,
    )
    build_interface(models).launch(
        server_name=args.server_name,
        server_port=args.server_port,
        show_error=True,
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run helper tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_web_app.py -v
```

Expected: 4 passed.

- [ ] **Step 4: Commit UI layer**

Run:

```powershell
git add web_app.py
git commit -m "Add Gradio image recognition UI"
```

## Task 4: Dependency Declaration and Smoke Checks

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add missing declared dependencies**

Append these lines to `requirements.txt` if they are not already present:

```text
gradio
pytest
```

- [ ] **Step 2: Run tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_web_app.py -v
```

Expected: 4 passed.

- [ ] **Step 3: Check the app help output**

Run:

```powershell
.\.venv\Scripts\python.exe web_app.py --help
```

Expected: argparse prints usage for `--detect_model`, `--rec_model`, `--img_size`, `--cpu`, `--server_name`, and `--server_port`.

- [ ] **Step 4: Start the app locally**

Run:

```powershell
.\.venv\Scripts\python.exe web_app.py --server_name 127.0.0.1 --server_port 7860
```

Expected: Gradio starts and prints a local URL.

- [ ] **Step 5: Commit dependencies**

Run:

```powershell
git add requirements.txt
git commit -m "Declare Gradio web UI dependencies"
```

## Task 5: Final Verification

**Files:**
- No file changes expected.

- [ ] **Step 1: Run focused tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_web_app.py -v
```

Expected: 4 passed.

- [ ] **Step 2: Confirm git status**

Run:

```powershell
git status --short
```

Expected: only the pre-existing untracked local result directories and `.venv/` remain.

- [ ] **Step 3: Report the local URL**

If the app is running, report `http://127.0.0.1:7860` to the user.
