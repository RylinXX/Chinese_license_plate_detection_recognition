import numpy as np
import pytest
from PIL import Image

from web_app import (
    ModelBundle,
    build_interface,
    format_camera_status,
    format_results,
    make_output_video_path,
    normalize_img_size,
    parse_args,
    pil_to_bgr,
    recognize_batch_images,
    recognize_camera_frame,
    recognize_image,
    recognize_video,
    validate_model_paths,
)


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


def test_format_results_handles_numpy_scalar_confidences():
    rows, message = format_results(
        [
            {
                "plate_no": "TEST999",
                "plate_color": "yellow",
                "detect_conf": np.array(0.95),
                "rec_conf": np.array(0.85),
                "plate_type": np.array(0),
            }
        ]
    )

    assert message == "Detected 1 license plate."
    assert rows[0]["detect_confidence"] == "0.950"
    assert rows[0]["recognition_confidence"] == "0.850"
    assert rows[0]["plate_type"] == "single"


def test_format_camera_status_reports_elapsed_time_and_fps():
    message = format_camera_status("Detected 1 license plate.", 0.25)

    assert message == "Detected 1 license plate. Inference time: 250 ms | Approx FPS: 4.00."


def test_pil_to_bgr_converts_rgb_image_to_bgr_array():
    image = Image.new("RGB", (2, 1), color=(10, 20, 30))

    result = pil_to_bgr(image)

    assert result.shape == (1, 2, 3)
    assert result.dtype == np.uint8
    assert result[0, 0].tolist() == [30, 20, 10]


def test_normalize_img_size_accepts_only_supported_sizes():
    assert normalize_img_size("1280") == 1280
    assert normalize_img_size(1280) == 1280
    assert normalize_img_size("640") == 640
    assert normalize_img_size("bad") == 640
    assert normalize_img_size(None) == 640


def test_validate_model_paths_reports_missing_file(tmp_path):
    existing = tmp_path / "detect.pt"
    missing = tmp_path / "rec.pth"
    existing.write_bytes(b"model")

    with pytest.raises(FileNotFoundError) as exc_info:
        validate_model_paths(str(existing), str(missing))

    assert str(missing) in str(exc_info.value)


def test_parse_args_uses_image_ui_defaults():
    args = parse_args([])

    assert args.detect_model == "weights/plate_detect.pt"
    assert args.rec_model == "weights/plate_rec_color.pth"
    assert args.img_size == 640
    assert args.is_color is True
    assert args.cpu is False
    assert args.server_name == "127.0.0.1"
    assert args.server_port == 7860


def test_recognize_image_runs_detector_and_drawer_with_selected_size():
    source = Image.new("RGB", (1, 1), color=(1, 2, 3))
    models = ModelBundle(
        detect_model="detect",
        rec_model="rec",
        device="cpu",
        img_size=640,
        is_color=True,
    )

    def fake_detector(detect_model, image, device, rec_model, img_size, is_color):
        assert detect_model == "detect"
        assert rec_model == "rec"
        assert device == "cpu"
        assert img_size == 1280
        assert is_color is True
        assert image[0, 0].tolist() == [3, 2, 1]
        return [
            {
                "plate_no": "TEST789",
                "plate_color": "green",
                "detect_conf": 0.99,
                "rec_conf": 0.88,
                "plate_type": 0,
            }
        ]

    def fake_drawer(image, results, is_color):
        assert results[0]["plate_no"] == "TEST789"
        assert is_color is True
        return image

    annotated, rows, message = recognize_image(
        source,
        models,
        img_size=1280,
        detector=fake_detector,
        drawer=fake_drawer,
    )

    assert annotated[0, 0].tolist() == [1, 2, 3]
    assert rows[0]["plate"] == "TEST789"
    assert message == "Detected 1 license plate."


def test_recognize_camera_frame_waits_for_first_frame():
    models = ModelBundle("detect", "rec", "cpu", 640, True)

    annotated, rows, message = recognize_camera_frame(None, models, 640)

    assert annotated is None
    assert rows == []
    assert message == "Waiting for camera frame."


def test_recognize_camera_frame_stops_without_running_detector():
    source = Image.new("RGB", (1, 1), color=(9, 8, 7))
    models = ModelBundle("detect", "rec", "cpu", 640, True)

    def fail_detector(*args):
        raise AssertionError("detector should not run when camera is stopped")

    annotated, rows, message = recognize_camera_frame(
        source,
        models,
        640,
        is_running=False,
        detector=fail_detector,
    )

    assert annotated is None
    assert rows == []
    assert message == "Camera recognition stopped."


def test_recognize_camera_frame_uses_selected_size():
    source = Image.new("RGB", (1, 1), color=(9, 8, 7))
    models = ModelBundle("detect", "rec", "cpu", 640, True)

    def fake_detector(detect_model, image, device, rec_model, img_size, is_color):
        assert img_size == 1280
        assert image[0, 0].tolist() == [7, 8, 9]
        return [
            {
                "plate_no": "CAM123",
                "plate_color": "blue",
                "detect_conf": 0.7,
                "rec_conf": 0.6,
                "plate_type": 0,
            }
        ]

    def fake_drawer(image, results, is_color):
        return image

    annotated, rows, message = recognize_camera_frame(
        source,
        models,
        1280,
        detector=fake_detector,
        drawer=fake_drawer,
    )

    assert annotated[0, 0].tolist() == [9, 8, 7]
    assert rows[0]["plate"] == "CAM123"
    assert message == "Detected 1 license plate."


def test_recognize_camera_frame_applies_mirror_correction():
    source = Image.new("RGB", (2, 1))
    source.putpixel((0, 0), (1, 2, 3))
    source.putpixel((1, 0), (9, 8, 7))
    models = ModelBundle("detect", "rec", "cpu", 640, True)

    def fake_detector(detect_model, image, device, rec_model, img_size, is_color):
        assert image[0, 0].tolist() == [7, 8, 9]
        return []

    def fake_drawer(image, results, is_color):
        return image

    annotated, rows, message = recognize_camera_frame(
        source,
        models,
        640,
        mirror_correction=True,
        detector=fake_detector,
        drawer=fake_drawer,
    )

    assert annotated[0, 0].tolist() == [9, 8, 7]
    assert rows == []
    assert message == "No license plate detected."


def test_build_interface_exposes_camera_interval_control_and_timer_update():
    models = ModelBundle("detect", "rec", "cpu", 640, True)

    demo = build_interface(models)
    components = demo.config["components"]
    interval_slider = next(
        component
        for component in components
        if component["type"] == "slider"
        and component["props"].get("label") == "Recognition interval (seconds)"
    )
    camera_timer = next(component for component in components if component["type"] == "timer")

    assert interval_slider["props"]["value"] == 0.7
    assert interval_slider["props"]["minimum"] == 0.2
    assert interval_slider["props"]["maximum"] == 2.0
    assert camera_timer["props"]["value"] == 0.7
    assert any(
        dependency["targets"] == [(interval_slider["id"], "change")]
        and dependency["outputs"] == [camera_timer["id"]]
        for dependency in demo.config["dependencies"]
    )


def test_recognize_batch_images_reports_empty_upload():
    models = ModelBundle("detect", "rec", "cpu", 640, True)

    gallery, summary, message = recognize_batch_images([], models, 640)

    assert gallery == []
    assert summary == []
    assert message == "No images were provided."


def test_recognize_batch_images_aggregates_files(tmp_path):
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"
    Image.new("RGB", (1, 1), color=(1, 2, 3)).save(first)
    Image.new("RGB", (1, 1), color=(4, 5, 6)).save(second)
    models = ModelBundle("detect", "rec", "cpu", 640, True)

    def fake_detector(detect_model, image, device, rec_model, img_size, is_color):
        assert img_size == 1280
        return [
            {
                "plate_no": "BATCH1",
                "plate_color": "blue",
                "detect_conf": 0.9,
                "rec_conf": 0.8,
                "plate_type": 0,
            }
        ]

    def fake_drawer(image, results, is_color):
        return image

    gallery, summary, message = recognize_batch_images(
        [str(first), str(second)],
        models,
        1280,
        detector=fake_detector,
        drawer=fake_drawer,
    )

    assert len(gallery) == 2
    assert len(summary) == 2
    assert summary[0]["filename"] == "first.jpg"
    assert summary[0]["results"][0]["plate"] == "BATCH1"
    assert message == "Processed 2 images."


def test_make_output_video_path_creates_mp4_path(tmp_path):
    output_path = make_output_video_path(tmp_path / "input.mov")

    assert output_path.parent == tmp_path
    assert output_path.suffix == ".mp4"
    assert "annotated" in output_path.name


def test_recognize_video_reports_missing_input():
    models = ModelBundle("detect", "rec", "cpu", 640, True)

    output, summary, message = recognize_video(None, models, 640)

    assert output is None
    assert summary == {"status": "No video was provided."}
    assert message == "No video was provided."


def test_recognize_video_reports_unreadable_path(tmp_path):
    models = ModelBundle("detect", "rec", "cpu", 640, True)

    output, summary, message = recognize_video(tmp_path / "missing.mp4", models, 640)

    assert output is None
    assert summary == {"status": "Could not open video."}
    assert message == "Could not open video."
