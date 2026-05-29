# Gradio Image Web UI Design

Date: 2026-05-29

## Goal

Add a local Gradio web interface for the existing license plate recognition project.
The first version supports image uploads only, so the user can preview the UI and
recognition quality before adding video support.

## Scope

In scope:

- Local browser UI launched from a Python entry point.
- Single image upload.
- Reuse the existing PyTorch detection and recognition pipeline.
- Display the annotated output image.
- Display recognized plate details in a compact table or JSON-like summary.
- Show clear error messages when input or model loading fails.

Out of scope for the first version:

- Video upload and video result rendering.
- Batch image upload.
- User accounts, persistence, deployment, or remote hosting.
- Training, model conversion, or accuracy changes.

## Recommended Approach

Use Gradio because it is the smallest useful layer over the current scripts.
The existing project already exposes reusable functions in `detect_plate.py`:

- `load_model`
- `detect_Recognition_plate`
- `draw_result`

The UI should import those functions, load the models once at startup, then run
inference for each uploaded image.

## Architecture

Add a new `web_app.py` file at the repository root.

Responsibilities:

- Parse optional CLI arguments for model paths, image size, device preference,
  and server host/port.
- Load the detection model and recognition model once during startup.
- Convert uploaded PIL images to OpenCV BGR arrays.
- Run the existing recognition pipeline.
- Draw detection results on a copy of the image.
- Convert the annotated BGR output back to RGB for Gradio display.
- Format recognition results for the UI.
- Build and launch the Gradio interface.

Keep model behavior inside the existing project functions. The web layer should
only adapt inputs and outputs.

## UI Design

The first screen is the actual tool, not a landing page.

Layout:

- A compact header naming the tool.
- Left side: image uploader and a recognize button.
- Right side: annotated image output.
- Below or beside the image: recognition details.

States:

- Empty state before upload.
- Processing state while inference runs.
- Success state with annotated image and result data.
- Error state with a short readable message.

## Data Flow

1. User uploads an image in the browser.
2. Gradio passes a PIL image to the prediction function.
3. The prediction function converts PIL RGB to OpenCV BGR.
4. The loaded detection model finds plate candidates.
5. The loaded recognition model reads plate text and color.
6. Existing drawing logic annotates the image.
7. The UI receives the annotated RGB image and formatted result rows.

## Error Handling

Handle these cases with user-facing messages:

- No image was provided.
- The uploaded image cannot be converted.
- Model files are missing or cannot be loaded.
- Inference raises an exception.
- No plate is detected.

Errors should not crash the Gradio server after startup.

## Testing

Add focused tests for web-layer helpers before implementing the UI:

- Formatting an empty recognition result returns a no-plate message.
- Formatting one or more recognition results exposes plate number, color,
  detection confidence, recognition confidence, and plate type.
- PIL-to-OpenCV conversion returns a BGR image with the expected shape.

Model inference itself will be verified by running the local Gradio app against
sample images after implementation.

## Acceptance Criteria

- `python web_app.py` starts a local Gradio web UI.
- A user can upload a license plate image from the browser.
- The UI shows an annotated image after recognition.
- The UI shows recognized plate information as text or tabular data.
- Existing command-line scripts still work.
- Helper tests pass.
