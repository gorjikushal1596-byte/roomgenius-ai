"""
backend/test_sam.py
-------------------
Unit tests for Meta SAM 3.1 segmentation service (Phase 1).
All tests run with 0 external API calls to conserve model credits.
"""

import json
from unittest.mock import MagicMock, patch
import pytest

from sam_service import (
    _sanitize_filename,
    generate_mock_segmentation,
    is_sam_configured,
    segment_furniture_image,
)
from schemas import NormalizedBoundingBox


def test_sanitize_filename():
    assert _sanitize_filename("room.jpg") == "room.jpg"
    assert _sanitize_filename("../../../etc/passwd.png") == "passwd.png"
    assert _sanitize_filename("my room photo (1).jpeg") == "my_room_photo__1_.jpeg"
    assert _sanitize_filename("") == "room_upload.jpg"


def test_bounding_box_validation():
    box = NormalizedBoundingBox(ymin=0.1, xmin=0.2, ymax=0.8, xmax=0.9)
    assert box.ymin == 0.1
    assert box.xmax == 0.9

    with pytest.raises(ValueError):
        # ymax cannot be less than ymin
        NormalizedBoundingBox(ymin=0.8, xmin=0.2, ymax=0.1, xmax=0.9)

    with pytest.raises(ValueError):
        # xmax cannot be less than xmin
        NormalizedBoundingBox(ymin=0.1, xmin=0.9, ymax=0.8, xmax=0.2)


def test_generate_mock_segmentation():
    res = generate_mock_segmentation("test_room.jpg")
    assert res.status == "success"
    assert res.total_detected == 4
    assert res.requires_user_calibration is True
    assert any(o.label == "Bed" for o in res.objects_detected)
    assert any(o.category == "sleeping" for o in res.objects_detected)
    assert all(o.calibrated is False for o in res.objects_detected)


def test_segment_empty_image_rejected():
    res = segment_furniture_image(b"", "empty.jpg", "image/jpeg")
    assert res.status == "error"
    assert res.total_detected == 0
    assert "empty" in res.message.lower()


def test_segment_oversized_image_rejected():
    huge_bytes = b"0" * (6 * 1024 * 1024)  # 6 MB
    res = segment_furniture_image(huge_bytes, "huge.jpg", "image/jpeg")
    assert res.status == "error"
    assert "exceeds maximum limit" in res.message


def test_segment_unsupported_mime_rejected():
    res = segment_furniture_image(b"fake-bytes", "test.gif", "image/gif")
    assert res.status == "error"
    assert "Unsupported image type" in res.message


def test_segment_force_mock():
    res = segment_furniture_image(b"fake-image-bytes", "living_room.png", "image/png", force_mock=True)
    assert res.status == "success"
    assert res.model_used == "sam-3.1-mock"
    assert len(res.objects_detected) > 0


def test_segment_handles_http_error():
    with patch("urllib.request.urlopen") as mock_urlopen:
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.meta.ai/v1/responses",
            code=429,
            msg="Rate limit",
            hdrs={},
            fp=MagicMock(read=lambda: b'{"error": "rate limit"}'),
        )

        with patch("sam_service._get_sam_config") as mock_cfg:
            mock_cfg.return_value = {
                "api_key": "dummy-key",
                "base_url": "https://api.meta.ai/v1",
                "model": "sam-3.1",
                "mock_mode": False,
            }
            res = segment_furniture_image(b"valid-image-bytes", "photo.jpg", "image/jpeg")
            assert res.status == "fallback"
            assert "fallback-due-to-http-429" in res.model_used
            assert len(res.objects_detected) > 0


def test_segment_handles_network_timeout():
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = TimeoutError("Connection timed out")

        with patch("sam_service._get_sam_config") as mock_cfg:
            mock_cfg.return_value = {
                "api_key": "dummy-key",
                "base_url": "https://api.meta.ai/v1",
                "model": "sam-3.1",
                "mock_mode": False,
            }
            res = segment_furniture_image(b"valid-image-bytes", "photo.jpg", "image/jpeg")
            assert res.status == "fallback"
            assert res.model_used == "fallback-due-to-network-error"
            assert len(res.objects_detected) > 0


def test_segment_parses_remote_boxes_correctly():
    fake_sam_response = json.dumps({
        "output": json.dumps([
            {
                "label": "sofa",
                "confidence": 0.94,
                "box": {"ymin": 0.3, "xmin": 0.2, "ymax": 0.7, "xmax": 0.8},
            },
            {
                "label": "coffee table",
                "confidence": 0.89,
                "box": {"ymin": 0.5, "xmin": 0.4, "ymax": 0.65, "xmax": 0.6},
            },
        ])
    }).encode("utf-8")

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value.read.return_value = fake_sam_response

        with patch("sam_service._get_sam_config") as mock_cfg:
            mock_cfg.return_value = {
                "api_key": "dummy-key",
                "base_url": "https://api.meta.ai/v1",
                "model": "sam-3.1",
                "mock_mode": False,
            }
            res = segment_furniture_image(b"valid-image-bytes", "living_room.jpg", "image/jpeg")
            assert res.status == "success"
            assert res.total_detected == 2
            assert res.objects_detected[0].label == "Sofa"
            assert res.objects_detected[0].category == "seating"
            assert res.objects_detected[0].calibrated is False
            assert res.objects_detected[1].category == "work"

