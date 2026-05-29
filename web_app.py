from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from typing import Any
from uuid import uuid4

import cv2
import numpy as np
from PIL import Image, ImageOps


@dataclass
class ModelBundle:
    detect_model: Any
    rec_model: Any
    device: Any
    img_size: int
    is_color: bool


def pil_to_bgr(image: Image.Image) -> np.ndarray:
    if image is None:
        raise ValueError("No image was provided.")
    rgb_image = image.convert("RGB")
    rgb_array = np.asarray(rgb_image, dtype=np.uint8)
    return cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)


def normalize_img_size(value: Any) -> int:
    try:
        size = int(value)
    except (TypeError, ValueError):
        return 640
    return 1280 if size == 1280 else 640


def _format_confidence(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            value = value.item()
        elif len(value) == 0:
            return ""
        else:
            value = float(np.mean(value))
    elif isinstance(value, (list, tuple)):
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


def format_camera_status(message: str, elapsed_seconds: float | None) -> str:
    if elapsed_seconds is None or elapsed_seconds <= 0:
        return message
    elapsed_ms = elapsed_seconds * 1000
    fps = 1 / elapsed_seconds
    return f"{message} Inference time: {elapsed_ms:.0f} ms | Approx FPS: {fps:.2f}."


Detector = Callable[[Any, np.ndarray, Any, Any, int, bool], list[dict[str, Any]]]
Drawer = Callable[[np.ndarray, list[dict[str, Any]], bool], np.ndarray]


def validate_model_paths(detect_model_path: str, rec_model_path: str) -> None:
    missing = [path for path in [detect_model_path, rec_model_path] if not Path(path).exists()]
    if missing:
        raise FileNotFoundError("Missing model file(s): " + ", ".join(missing))


def load_models(
    detect_model_path: str,
    rec_model_path: str,
    img_size: int,
    is_color: bool,
    force_cpu: bool,
) -> ModelBundle:
    import torch
    from detect_plate import load_model
    from plate_recognition.plate_rec import init_model

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


def _default_detector() -> Detector:
    from detect_plate import detect_Recognition_plate

    return detect_Recognition_plate


def _default_drawer() -> Drawer:
    from detect_plate import draw_result

    return draw_result


def recognize_image(
    image: Image.Image,
    models: ModelBundle,
    img_size: Any | None = None,
    detector: Detector | None = None,
    drawer: Drawer | None = None,
) -> tuple[np.ndarray | None, list[dict[str, str]], str]:
    try:
        bgr_image = pil_to_bgr(image)
        detector = detector or _default_detector()
        drawer = drawer or _default_drawer()
        selected_size = normalize_img_size(img_size if img_size is not None else models.img_size)
        results = detector(
            models.detect_model,
            bgr_image,
            models.device,
            models.rec_model,
            selected_size,
            models.is_color,
        )
        annotated_bgr = drawer(bgr_image.copy(), results, models.is_color)
        rows, message = format_results(results)
        annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
        return annotated_rgb, rows, message
    except ValueError as exc:
        return None, [], str(exc)
    except Exception as exc:
        return None, [], f"Recognition failed: {exc}"


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
    return recognize_image(
        image,
        models,
        img_size=img_size,
        detector=detector,
        drawer=drawer,
    )


def _uploaded_file_path(file: Any) -> Path | None:
    if file is None:
        return None
    if isinstance(file, (str, Path)):
        return Path(file)
    name = getattr(file, "name", None)
    if name:
        return Path(name)
    path = getattr(file, "path", None)
    if path:
        return Path(path)
    return None


def recognize_batch_images(
    files: list[Any] | None,
    models: ModelBundle,
    img_size: Any,
    detector: Detector | None = None,
    drawer: Drawer | None = None,
) -> tuple[list[tuple[np.ndarray, str]], list[dict[str, Any]], str]:
    if not files:
        return [], [], "No images were provided."

    gallery = []
    summary = []
    for file in files:
        path = _uploaded_file_path(file)
        filename = path.name if path else "unknown"
        if path is None:
            summary.append({"filename": filename, "status": "Could not read image file.", "results": []})
            continue
        try:
            with Image.open(path) as image:
                annotated, rows, message = recognize_image(
                    image,
                    models,
                    img_size=img_size,
                    detector=detector,
                    drawer=drawer,
                )
            if annotated is not None:
                gallery.append((annotated, filename))
            summary.append({"filename": filename, "status": message, "results": rows})
        except Exception as exc:
            summary.append({"filename": filename, "status": f"Recognition failed: {exc}", "results": []})

    noun = "image" if len(files) == 1 else "images"
    return gallery, summary, f"Processed {len(files)} {noun}."


def make_output_video_path(input_path: str | Path) -> Path:
    path = Path(input_path)
    return path.with_name(f"{path.stem}_annotated_{uuid4().hex[:8]}.mp4")


def recognize_video(
    video: Any,
    models: ModelBundle,
    img_size: Any,
    detector: Detector | None = None,
    drawer: Drawer | None = None,
    output_path: str | Path | None = None,
) -> tuple[str | None, dict[str, Any], str]:
    path = _uploaded_file_path(video)
    if path is None:
        message = "No video was provided."
        return None, {"status": message}, message

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        message = "Could not open video."
        capture.release()
        return None, {"status": message}, message

    detector = detector or _default_detector()
    drawer = drawer or _default_drawer()
    selected_size = normalize_img_size(img_size)
    output = Path(output_path) if output_path is not None else make_output_video_path(path)
    writer = None
    frame_count = 0
    detected_frames = []

    try:
        fps = capture.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 0:
            fps = 25.0

        while True:
            ok, frame = capture.read()
            if not ok:
                break

            frame_count += 1
            if writer is None:
                height, width = frame.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(str(output), fourcc, fps, (width, height))
                if not writer.isOpened():
                    message = "Could not create output video."
                    return None, {"status": message}, message

            results = detector(
                models.detect_model,
                frame,
                models.device,
                models.rec_model,
                selected_size,
                models.is_color,
            )
            annotated_frame = drawer(frame.copy(), results, models.is_color)
            writer.write(annotated_frame)
            rows, _ = format_results(results)
            if rows:
                detected_frames.append({"frame": frame_count, "results": rows})

        if frame_count == 0:
            message = "No frames were read from video."
            return None, {"status": message, "frames": 0}, message

        message = f"Processed {frame_count} video frames."
        return (
            str(output),
            {"status": message, "frames": frame_count, "detections": detected_frames},
            message,
        )
    except Exception as exc:
        message = f"Video recognition failed: {exc}"
        return None, {"status": message, "frames": frame_count, "detections": detected_frames}, message
    finally:
        capture.release()
        if writer is not None:
            writer.release()


def build_interface(models: ModelBundle) -> Any:
    import gradio as gr

    def predict(image: Image.Image, img_size: int) -> tuple[np.ndarray | None, list[dict[str, str]], str]:
        return recognize_image(image, models, img_size=img_size)

    def predict_batch(files: list[Any], img_size: int) -> tuple[list[tuple[np.ndarray, str]], list[dict[str, Any]], str]:
        return recognize_batch_images(files, models, img_size=img_size)

    def predict_video(video: Any, img_size: int) -> tuple[str | None, dict[str, Any], str]:
        return recognize_video(video, models, img_size=img_size)

    def predict_camera(
        image: Image.Image | None,
        img_size: int,
        mirror_correction: bool,
        is_running: bool,
        interval: float,
    ) -> tuple[np.ndarray | None, list[dict[str, str]], str]:
        start_time = time.perf_counter()
        annotated, rows, message = recognize_camera_frame(
            image,
            models,
            img_size=img_size,
            mirror_correction=mirror_correction,
            is_running=is_running,
        )
        if not is_running or image is None:
            return annotated, rows, message
        status = format_camera_status(message, time.perf_counter() - start_time)
        return annotated, rows, f"{status} Interval: {float(interval):.2f} s."

    def start_camera() -> tuple[bool, str]:
        return True, "Camera recognition started."

    def stop_camera() -> tuple[bool, str]:
        return False, "Camera recognition stopped."

    def update_camera_interval(interval: float) -> float:
        return float(interval)

    with gr.Blocks(title="License Plate Recognition") as demo:
        gr.Markdown("# License Plate Recognition")

        with gr.Tab("Single Image"):
            with gr.Row():
                with gr.Column(scale=1):
                    image_input = gr.Image(type="pil", label="Input image")
                    image_size = gr.Radio([640, 1280], value=640, label="Recognition size")
                    recognize_button = gr.Button("Recognize", variant="primary")
                with gr.Column(scale=1):
                    image_output = gr.Image(type="numpy", label="Annotated result")

            result_output = gr.JSON(label="Recognition details")
            status_output = gr.Textbox(label="Status", interactive=False)
            recognize_button.click(
                fn=predict,
                inputs=[image_input, image_size],
                outputs=[image_output, result_output, status_output],
            )

        with gr.Tab("Batch Images"):
            with gr.Row():
                with gr.Column(scale=1):
                    batch_input = gr.File(
                        file_count="multiple",
                        file_types=["image"],
                        label="Input images",
                    )
                    batch_size = gr.Radio([640, 1280], value=640, label="Recognition size")
                    batch_button = gr.Button("Recognize Batch", variant="primary")
                with gr.Column(scale=1):
                    batch_gallery = gr.Gallery(label="Annotated results")

            batch_result = gr.JSON(label="Batch recognition details")
            batch_status = gr.Textbox(label="Batch status", interactive=False)
            batch_button.click(
                fn=predict_batch,
                inputs=[batch_input, batch_size],
                outputs=[batch_gallery, batch_result, batch_status],
            )

        with gr.Tab("Video"):
            with gr.Row():
                with gr.Column(scale=1):
                    video_input = gr.Video(label="Input video")
                    video_size = gr.Radio([640, 1280], value=640, label="Recognition size")
                    video_button = gr.Button("Recognize Video", variant="primary")
                with gr.Column(scale=1):
                    video_output = gr.Video(label="Annotated video")

            video_result = gr.JSON(label="Video recognition details")
            video_status = gr.Textbox(label="Video status", interactive=False)
            video_button.click(
                fn=predict_video,
                inputs=[video_input, video_size],
                outputs=[video_output, video_result, video_status],
            )

        with gr.Tab("Camera"):
            camera_running = gr.State(False)
            camera_timer = gr.Timer(0.7, active=True)
            with gr.Row():
                with gr.Column(scale=1):
                    camera_input = gr.Image(
                        sources="webcam",
                        streaming=True,
                        type="pil",
                        label="Camera",
                    )
                    camera_size = gr.Radio([640, 1280], value=640, label="Recognition size")
                    camera_mirror = gr.Checkbox(value=True, label="Mirror correction")
                    camera_interval = gr.Slider(
                        minimum=0.2,
                        maximum=2.0,
                        value=0.7,
                        step=0.1,
                        label="Recognition interval (seconds)",
                    )
                    with gr.Row():
                        camera_start = gr.Button("Start Recognition", variant="primary")
                        camera_stop = gr.Button("Stop Recognition")
                with gr.Column(scale=1):
                    camera_output = gr.Image(type="numpy", label="Annotated camera frame")

            camera_result = gr.JSON(label="Camera recognition details")
            camera_status = gr.Textbox(label="Camera status", interactive=False)
            camera_start.click(
                fn=start_camera,
                outputs=[camera_running, camera_status],
            )
            camera_stop.click(
                fn=stop_camera,
                outputs=[camera_running, camera_status],
            )
            camera_interval.change(
                fn=update_camera_interval,
                inputs=camera_interval,
                outputs=camera_timer,
            )
            camera_timer.tick(
                fn=predict_camera,
                inputs=[camera_input, camera_size, camera_mirror, camera_running, camera_timer],
                outputs=[camera_output, camera_result, camera_status],
                trigger_mode="always_last",
                concurrency_limit=1,
            )

    return demo


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Gradio image recognition UI.")
    parser.add_argument("--detect_model", default="weights/plate_detect.pt")
    parser.add_argument("--rec_model", default="weights/plate_rec_color.pth")
    parser.add_argument("--img_size", type=int, default=640)
    parser.add_argument("--is_color", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--cpu", action="store_true", help="Force CPU inference.")
    parser.add_argument("--server_name", default="127.0.0.1")
    parser.add_argument("--server_port", type=int, default=7860)
    return parser.parse_args(argv)


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
