"""
backend/test_depth.py
---------------------
Unit tests for Depth Anything V2 depth estimation service (Phase 1).
All tests execute with 0 external API calls to conserve resources and credits.
"""

import pytest

from depth_service import (
    _compute_box_depth,
    _get_image_hash,
    clear_depth_cache,
    estimate_room_depth,
    generate_mock_depth_map,
    is_depth_configured,
)
from schemas import (
    DepthEstimationRequest,
    NormalizedBoundingBox,
)


@pytest.fixture(autouse=True)
def clean_cache():
    clear_depth_cache()
    yield
    clear_depth_cache()


def test_depth_service_is_configured():
    assert is_depth_configured() is True


def test_get_image_hash_deterministic():
    data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    h1 = _get_image_hash(data)
    h2 = _get_image_hash(data)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256


def test_compute_box_depth_perspective_ordering():
    # In perspective indoor photos:
    # Foreground box is near the bottom (ymin=0.7, ymax=0.95)
    foreground_box = NormalizedBoundingBox(ymin=0.7, xmin=0.2, ymax=0.95, xmax=0.5)
    # Background box is near the horizon/top (ymin=0.1, ymax=0.35)
    background_box = NormalizedBoundingBox(ymin=0.1, xmin=0.2, ymax=0.35, xmax=0.5)

    near_depth = _compute_box_depth(foreground_box, max_room_depth_m=6.0)
    far_depth = _compute_box_depth(background_box, max_room_depth_m=6.0)

    # Foreground object must be closer to camera (smaller depth in meters)
    assert near_depth < far_depth
    assert near_depth >= 0.8
    assert far_depth <= 6.0


def test_generate_mock_depth_map_structure():
    req = DepthEstimationRequest(
        image_base64="fake-b64-data",
        filename="room.jpg",
    )
    res = generate_mock_depth_map(req)
    assert res.status == "success"
    assert res.depth_map_data.startswith("data:image/svg+xml;base64,")
    assert res.min_depth_m > 0
    assert res.max_depth_m >= 2.0
    assert "Monocular depth estimates provide relative spatial ordering" in res.disclaimer


def test_generate_mock_depth_map_with_boxes():
    boxes = [
        # Near coffee table (bottom of frame)
        NormalizedBoundingBox(ymin=0.7, xmin=0.3, ymax=0.9, xmax=0.7),
        # Midground sofa
        NormalizedBoundingBox(ymin=0.4, xmin=0.2, ymax=0.6, xmax=0.8),
        # Far wardrobe (top of frame)
        NormalizedBoundingBox(ymin=0.1, xmin=0.1, ymax=0.35, xmax=0.4),
    ]
    req = DepthEstimationRequest(
        image_base64="fake-b64-data",
        filename="living_room.png",
        detected_boxes=boxes,
    )
    res = generate_mock_depth_map(req)
    assert res.status == "success"
    assert len(res.object_depth_profiles) == 3

    # Check ordering
    p_near = res.object_depth_profiles[0]
    p_mid = res.object_depth_profiles[1]
    p_far = res.object_depth_profiles[2]

    assert p_near.median_depth_m < p_mid.median_depth_m < p_far.median_depth_m
    assert p_near.relative_layer == "foreground"
    assert p_far.relative_layer == "background"


def test_generate_mock_depth_map_scales_with_calibrated_room_length():
    # Long 8-meter gallery room (800 cm)
    req_long = DepthEstimationRequest(
        image_base64="fake-b64-data",
        calibrated_room_length_cm=800.0,
    )
    res_long = generate_mock_depth_map(req_long)
    assert res_long.max_depth_m == 8.0

    # Compact 3-meter studio (300 cm)
    req_compact = DepthEstimationRequest(
        image_base64="fake-b64-data",
        calibrated_room_length_cm=300.0,
    )
    res_compact = generate_mock_depth_map(req_compact)
    assert res_compact.max_depth_m == 3.0


def test_estimate_room_depth_empty_image_error():
    req = DepthEstimationRequest(image_base64="")
    res = estimate_room_depth(req)
    assert res.status == "error"
    assert "Empty image payload" in res.disclaimer


def test_estimate_room_depth_caching_behavior():
    req = DepthEstimationRequest(
        image_base64="unique-image-payload-abc-123",
        filename="room.jpg",
    )
    # First call: computes and caches
    res1 = estimate_room_depth(req)
    assert res1.status == "success"

    # Second call with identical payload: returns cached reference
    res2 = estimate_room_depth(req)
    assert res2.status == "success"
    assert res1.depth_map_data == res2.depth_map_data
    assert res1.processing_time_ms == res2.processing_time_ms

