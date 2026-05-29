# Gradio Local Camera Web UI Design

Date: 2026-05-29

## Goal

Add a local camera test tab to the existing Gradio license plate recognition UI.
The first version is for quick browser-based webcam testing, not a production
streaming service.

## Scope

In scope:

- Add a `Camera` tab.
- Use the browser's local webcam through Gradio.
- Stream camera frames into the existing single-frame recognition pipeline.
- Show an annotated live frame.
- Show the current frame's recognition JSON and status message.
- Reuse the existing `640` / `1280` recognition size control.
- Provide explicit start/stop controls for camera recognition.
- Provide a mirror correction toggle for browser webcam frames.

Out of scope:

- RTSP/network camera support.
- Backend `cv2.VideoCapture(0)` camera ownership.
- Multi-camera routing.
- Recording camera streams to disk.
- Production WebSocket/MJPEG streaming service.

## Recommended Approach

Use `gr.Image(sources="webcam", streaming=True, type="pil")` inside a new
`Camera` tab. A Gradio `Timer` polls the latest camera frame while a
`camera_running` state is true. This gives the UI explicit start/stop controls
instead of relying only on Gradio's webcam stream event.

This keeps the camera feature aligned with the current web architecture: Gradio
collects the input, `web_app.py` adapts it, and the existing detector/recognizer
functions do the model work.

## Data Flow

1. The user opens the `Camera` tab.
2. The browser asks for local camera permission.
3. The user clicks `Start Recognition`.
4. A Gradio timer reads the latest webcam frame.
5. If mirror correction is enabled, the frame is flipped horizontally before
   inference.
6. The frame is converted to OpenCV BGR.
7. Existing detection and recognition functions run on that frame.
8. The annotated frame is returned to the UI.
9. The current frame's recognition rows and status are shown as JSON/text.
10. The user clicks `Stop Recognition` to stop backend recognition polling.

## Error Handling

- Before a camera frame arrives, show `Waiting for camera frame.`
- When recognition is stopped, show `Camera recognition stopped.`
- If a frame cannot be processed, return no annotated frame and a readable
  error message.
- If no plate is detected, keep the frame output and show the existing
  no-plate status.

## Testing

Add helper tests that avoid loading model weights:

- `recognize_camera_frame(None, ...)` returns a waiting status.
- `recognize_camera_frame(..., is_running=False)` returns a stopped status.
- `recognize_camera_frame(..., mirror_correction=True)` flips the frame before
  recognition.
- `recognize_camera_frame(image, ..., img_size=1280)` passes the selected size
  to the detector and returns the expected annotated frame and rows.

Manual/browser verification:

- Start `web_app.py`.
- Confirm the `Camera` tab renders.
- Confirm webcam input and `640` / `1280` controls render.

## Acceptance Criteria

- The Web UI includes a `Camera` tab.
- The camera input uses browser webcam capture.
- Camera recognition has visible start and stop controls.
- Camera recognition has a mirror correction toggle.
- Camera frame recognition reuses existing model loading and inference helpers.
- The user can select `640` or `1280` for camera recognition.
- Existing image, batch image, and video tabs still render.
- Focused helper tests pass.
