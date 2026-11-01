"""
backend/test_api_extensions.py
------------------------------
Integration tests for new Phase 2 FastAPI endpoints:
- GET /ai/models-status
- POST /ai/segment-furniture
- POST /ai/generate-preview

Zero credits consumed: all tests run using mock services / mock fixtures.
"""

import base64
from fastapi.testclient import TestClient
import pytest

from main import app, _sam_semaphore, _muse_image_semaphore, _depth_semaphore

client = TestClient(app)


def test_models_status_endpoint():
    res = client.get("/ai/models-status")
    assert res.status_code == 200
    data = res.json()
    assert "muse_spark" in data
    assert "sam_3_1" in data
    assert "muse_image" in data
    assert "depth_anything_v2" in data


def test_segment_furniture_endpoint_valid_base64():
    # 1x1 transparent png
    tiny_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    payload = {
        "image_base64": tiny_b64,
        "filename": "my_bedroom.png",
        "mime_type": "image/png",
    }
    res = client.post("/ai/segment-furniture", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("success", "fallback")
    assert "objects_detected" in data
    assert data["requires_user_calibration"] is True


def test_segment_furniture_endpoint_data_uri():
    tiny_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    data_uri = f"data:image/png;base64,{tiny_b64}"
    payload = {
        "image_base64": data_uri,
        "filename": "living_room.png",
    }
    res = client.post("/ai/segment-furniture", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("success", "fallback")
    assert len(data["objects_detected"]) > 0


def test_segment_furniture_endpoint_invalid_base64():
    payload = {
        "image_base64": "not-valid-base64-content!!!!",
        "filename": "corrupt.jpg",
    }
    res = client.post("/ai/segment-furniture", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "error"
    assert "Invalid base64" in data["message"]


def test_segment_furniture_concurrency_busy():
    # Acquire the semaphore to simulate a busy background request
    acquired = _sam_semaphore.acquire(blocking=False)
    assert acquired is True
    try:
        tiny_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        payload = {
            "image_base64": tiny_b64,
            "filename": "busy_room.png",
        }
        res = client.post("/ai/segment-furniture", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "fallback"
        assert data["model_used"] == "fallback-server-busy"
        assert len(data["objects_detected"]) > 0
    finally:
        _sam_semaphore.release()


def test_generate_preview_endpoint_valid_payload():
    payload = {
        "room_width_cm": 420.0,
        "room_length_cm": 520.0,
        "style": "scandinavian modern",
        "placed_items": [
            {
                "id": "bed-1",
                "name": "Platform Bed",
                "placed": True,
                "x": 60.0,
                "y": 60.0,
                "width": 160.0,
                "length": 200.0,
                "rotation": 0,
                "within_bounds": True,
            }
        ],
        "custom_prompt_additions": "ash wood flooring and soft linen curtains",
    }
    res = client.post("/ai/generate-preview", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("success", "fallback")
    assert "image_data" in data
    assert "Aesthetic concept preview only" in data["disclaimer"]


def test_generate_preview_concurrency_busy():
    # Acquire the semaphore to simulate a busy preview generation
    acquired = _muse_image_semaphore.acquire(blocking=False)
    assert acquired is True
    try:
        payload = {
            "room_width_cm": 300.0,
            "room_length_cm": 400.0,
            "style": "minimalist",
            "placed_items": [],
        }
        res = client.post("/ai/generate-preview", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "fallback"
        assert data["model_used"] == "fallback-server-busy"
        assert "image_data" in data
    finally:
        _muse_image_semaphore.release()


def test_estimate_depth_endpoint_valid_payload():
    tiny_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    payload = {
        "image_base64": tiny_b64,
        "filename": "room_shot.jpg",
        "calibrated_room_length_cm": 450.0,
        "detected_boxes": [
            {"ymin": 0.2, "xmin": 0.2, "ymax": 0.5, "xmax": 0.6},
            {"ymin": 0.7, "xmin": 0.3, "ymax": 0.9, "xmax": 0.7},
        ],
    }
    res = client.post("/ai/estimate-depth", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("success", "fallback")
    assert "depth_map_data" in data
    assert len(data["object_depth_profiles"]) == 2
    assert "Monocular depth estimates provide relative spatial ordering" in data["disclaimer"]


def test_estimate_depth_concurrency_busy():
    # Acquire the semaphore to simulate a busy depth calculation
    acquired = _depth_semaphore.acquire(blocking=False)
    assert acquired is True
    try:
        tiny_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        payload = {
            "image_base64": tiny_b64,
            "filename": "room_busy.jpg",
        }
        res = client.post("/ai/estimate-depth", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "fallback"
        assert data["model_used"] == "fallback-server-busy"
        assert "depth_map_data" in data
    finally:
        _depth_semaphore.release()


