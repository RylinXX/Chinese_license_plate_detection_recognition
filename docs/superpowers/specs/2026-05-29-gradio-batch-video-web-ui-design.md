# Gradio Batch Image and Video Web UI Design

Date: 2026-05-29

## Goal

Extend the existing Gradio image UI so it can also process multiple images and
videos from the browser.

## Scope

In scope:

- Keep the existing single-image tab.
- Add a batch image tab that accepts multiple uploaded image files.
- Show batch image outputs as a gallery of annotated images.
- Show batch image recognition results as a JSON summary grouped by filename.
- Add a video tab that accepts one uploaded video.
- Write an annotated MP4 video and return it for preview or download.
- Show a compact video summary with frame counts and detected plate rows.
- Add a recognition size control with `640` and `1280` options.

Out of scope:

- ZIP download management.
- Background job queues.
- Progress bars beyond Gradio's normal running state.
- Model retraining or accuracy tuning.

## Recommended Approach

Use three Gradio tabs:

- Single Image
- Batch Images
- Video

All tabs reuse the same loaded `ModelBundle`. The Web layer should continue to
adapt inputs and outputs only; detection and drawing stay in the existing model
functions.

The recognition size control is available on each tab and defaults to `640`.
When the user selects `1280`, the same loaded models are reused but inference is
called with `img_size=1280`. This helps small plates in wide images without
requiring a server restart.

## Data Flow

### Batch Images

1. User uploads multiple image files.
2. Each file is opened with Pillow.
3. Existing image recognition logic runs once per image.
4. The selected recognition size is passed to each image inference call.
5. Annotated images are returned to a Gradio gallery.
6. A JSON summary lists each file, status message, and recognition rows.

### Video

1. User uploads one video file.
2. OpenCV reads frames from the uploaded path.
3. Each frame is sent through the existing detection and drawing functions.
4. The selected recognition size is passed to each frame inference call.
5. Annotated frames are written to a temporary MP4 file.
6. The UI returns the output video path and a JSON summary.

## Error Handling

- Empty batch upload returns an empty gallery and a readable status.
- A single bad image in a batch records an error for that file and continues.
- Missing or unreadable video returns no output video and a readable status.
- Video writer failures return no output video and a readable status.
- Inference exceptions are captured in the relevant image or video summary.

## Testing

Add helper tests that avoid loading model weights:

- Batch processing aggregates multiple fake image results by filename.
- Empty batch upload returns a clear message.
- Video output path helper creates an `.mp4` path in a temporary directory.
- Video processing handles unreadable input paths with a readable status.

Manual/integration verification:

- Start `web_app.py`.
- Upload two sample images and confirm gallery plus JSON results render.
- Upload a small sample video when available and confirm an output MP4 is
  produced.

## Acceptance Criteria

- The Web UI has tabs for single image, batch images, and video.
- Batch images can be uploaded together.
- Batch output shows annotated images in a gallery.
- Batch output includes per-file recognition JSON.
- Video upload returns an annotated MP4 path for preview or download.
- The user can choose recognition size `640` or `1280` in the Web UI.
- Existing single-image behavior still works.
- Focused helper tests pass.
