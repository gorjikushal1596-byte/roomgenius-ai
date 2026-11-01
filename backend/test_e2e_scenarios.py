"""
backend/test_e2e_scenarios.py
-----------------------------
Comprehensive Day 6 End-to-End & Reliability Test Suite for RoomGenius AI.
Verifies all 11 required scenarios:
  1. Normal rectangular room with multiple furniture items
  2. Very small room with oversized furniture
  3. Furniture that cannot fit inside room boundaries
  4. Multiple furniture items that could overlap
  5. Invalid or missing room dimensions
  6. Zero or negative furniture dimensions
  7. Unsupported rotation values
  8. Empty furniture list
  9. Partial layout where not every item fits
  10. Repeated identical requests (deterministic idempotency)
  11. Integrity: Never present an overlapping or out-of-bounds layout as successful
  12. AI explanation graceful fallback on simulated outage
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from geometry import Rect, get_oriented_dimensions, rectangles_overlap

client = TestClient(app)


# ---------------------------------------------------------------------------
# Scenario 1: Normal rectangular room with multiple furniture items
# ---------------------------------------------------------------------------
def test_scenario_normal_room_multiple_items_complete_e2e():
    """Verify standard room layout generates feasible placements and valid AI explanation."""
    payload = {
        "width": 400.0,
        "length": 500.0,
        "height": 270.0,
        "unit": "cm",
        "furniture": [
            {"id": "bed-1", "name": "Queen Bed", "width": 160.0, "length": 200.0},
            {"id": "desk-1", "name": "Study Desk", "width": 120.0, "length": 60.0},
            {"id": "wardrobe-1", "name": "2-Door Wardrobe", "width": 100.0, "length": 60.0},
        ],
        "preferences": {"style": "minimalist", "focus": "natural light"},
    }
    # 1. Generate Layout
    res = client.post("/layout", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["feasible"] is True
    assert data["summary"]["placed_count"] == 3
    assert data["summary"]["unplaced_count"] == 0
    assert len(data["placed_items"]) == 3

    # Verify zero overlaps among placed items
    placed = data["placed_items"]
    rects = [Rect(x=p["x"], y=p["y"], width=p["width"], length=p["length"]) for p in placed]
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            assert not rectangles_overlap(rects[i], rects[j]), f"Overlap between {placed[i]['id']} and {placed[j]['id']}"

    # 2. Request AI Explanation (using mock mode to conserve credits)
    ai_payload = {
        "room_width_cm": data["summary"]["room_width_cm"],
        "room_length_cm": data["summary"]["room_length_cm"],
        "room_height_cm": data["summary"]["room_height_cm"],
        "preferences": payload["preferences"],
        "placed_items": data["placed_items"],
        "unplaced_items": data["unplaced_items"],
    }
    with patch("ai._get_env_config") as mock_cfg:
        mock_cfg.return_value = {
            "api_key": "",
            "base_url": "https://api.meta.ai/v1",
            "model": "muse-spark-1.3",
            "mock_mode": True,
        }
        ai_res = client.post("/ai/explain", json=ai_payload)
        assert ai_res.status_code == 200
        ai_data = ai_res.json()
        assert ai_data["status"] == "success"
        assert len(ai_data["arrangement_tips"]) >= 2
        assert "Queen Bed" in ai_data["summary"]


# ---------------------------------------------------------------------------
# Scenario 2: Very small room with oversized furniture
# ---------------------------------------------------------------------------
def test_scenario_very_small_room_oversized_furniture():
    """Verify that furniture larger than room boundaries is rejected."""
    payload = {
        "width": 100.0,
        "length": 100.0,
        "furniture": [
            {"id": "bed-huge", "name": "King Bed", "width": 200.0, "length": 180.0}
        ],
    }
    res = client.post("/layout", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["feasible"] is False
    assert data["summary"]["placed_count"] == 0
    assert data["summary"]["unplaced_count"] == 1
    assert data["unplaced_items"][0]["placed"] is False
    assert "exceed room boundaries" in data["unplaced_items"][0]["rejection_reason"]


# ---------------------------------------------------------------------------
# Scenario 3: Furniture that cannot fit inside room boundaries
# ---------------------------------------------------------------------------
def test_scenario_furniture_cannot_fit_boundaries():
    """Verify single dimension exceeding boundary rejects item even if area is small."""
    payload = {
        "width": 200.0,
        "length": 200.0,
        "furniture": [
            {"id": "pole-1", "name": "Long Runner Rug", "width": 250.0, "length": 50.0}
        ],
    }
    res = client.post("/layout", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["feasible"] is False
    assert data["summary"]["placed_count"] == 0
    assert data["unplaced_items"][0]["id"] == "pole-1"


# ---------------------------------------------------------------------------
# Scenario 4: Multiple furniture items that could overlap
# ---------------------------------------------------------------------------
def test_scenario_multiple_items_potential_overlap():
    """Verify that tight packing of 4 equal quadrants yields zero positive-area overlap."""
    payload = {
        "width": 200.0,
        "length": 200.0,
        "furniture": [
            {"id": "box-1", "name": "Cabinet A", "width": 100.0, "length": 100.0},
            {"id": "box-2", "name": "Cabinet B", "width": 100.0, "length": 100.0},
            {"id": "box-3", "name": "Cabinet C", "width": 100.0, "length": 100.0},
            {"id": "box-4", "name": "Cabinet D", "width": 100.0, "length": 100.0},
        ],
    }
    res = client.post("/layout", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["feasible"] is True
    assert data["summary"]["placed_count"] == 4

    rects = [Rect(x=p["x"], y=p["y"], width=p["width"], length=p["length"]) for p in data["placed_items"]]
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            assert not rectangles_overlap(rects[i], rects[j])


# ---------------------------------------------------------------------------
# Scenario 5: Invalid or missing room dimensions
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "invalid_payload",
    [
        {"length": 400.0, "furniture": []},  # Missing width
        {"width": 300.0, "furniture": []},   # Missing length
        {"width": "abc", "length": 400.0},   # Non-numeric width
        {"width": "Infinity", "length": 400.0}, # Non-finite string
        {"width": 999999.0, "length": 400.0},   # Exceeds max allowed dimension
        {"width": -50.0, "length": 400.0},   # Negative width
        {"width": 0.0, "length": 400.0},     # Zero width
    ],
)
def test_scenario_invalid_or_missing_room_dimensions(invalid_payload):
    """Verify validation rejects invalid room dimensions with HTTP 422."""
    res = client.post("/layout", json=invalid_payload)
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Scenario 6: Zero or negative furniture dimensions
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "item_w,item_l",
    [
        (0.0, 100.0),
        (-10.0, 100.0),
        (100.0, 0.0),
        (100.0, -50.0),
    ],
)
def test_scenario_zero_or_negative_furniture_dimensions(item_w, item_l):
    """Verify validation rejects zero or negative furniture dimensions with HTTP 422."""
    payload = {
        "width": 300.0,
        "length": 300.0,
        "furniture": [{"id": "bad-1", "name": "Bad Item", "width": item_w, "length": item_l}],
    }
    res = client.post("/layout", json=payload)
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Scenario 7: Unsupported rotation values
# ---------------------------------------------------------------------------
def test_scenario_unsupported_rotation_values():
    """Verify that geometry function strictly rejects non-0/90 degree rotations."""
    with pytest.raises(ValueError, match="Unsupported rotation: 45°"):
        get_oriented_dimensions(100.0, 50.0, rotation=45)

    with pytest.raises(ValueError, match="Unsupported rotation: 180°"):
        get_oriented_dimensions(100.0, 50.0, rotation=180)


# ---------------------------------------------------------------------------
# Scenario 8: Empty furniture list
# ---------------------------------------------------------------------------
def test_scenario_empty_furniture_list():
    """Verify valid empty room produces 200 accepted and feasible=True."""
    payload = {"width": 350.0, "length": 450.0, "furniture": []}
    res = client.post("/layout", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["feasible"] is True
    assert data["summary"]["furniture_count"] == 0
    assert data["summary"]["placed_count"] == 0
    assert data["summary"]["unplaced_count"] == 0
    assert data["placed_items"] == []
    assert data["unplaced_items"] == []


# ---------------------------------------------------------------------------
# Scenario 9: Partial layout where not every item fits
# ---------------------------------------------------------------------------
def test_scenario_partial_layout_crowded_room():
    """Verify crowded room reports partial layout with feasible=False and explicit rejections."""
    payload = {
        "width": 200.0,
        "length": 200.0,
        "furniture": [
            {"id": "table-1", "name": "Large Dining Table", "width": 160.0, "length": 140.0},
            {"id": "sofa-1", "name": "2-Seater Sofa", "width": 150.0, "length": 100.0},
        ],
    }
    res = client.post("/layout", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["feasible"] is False
    assert data["summary"]["placed_count"] == 1
    assert data["summary"]["unplaced_count"] == 1
    assert data["placed_items"][0]["id"] == "table-1"
    assert data["unplaced_items"][0]["id"] == "sofa-1"
    assert data["unplaced_items"][0]["rejection_reason"] is not None


# ---------------------------------------------------------------------------
# Scenario 10: Repeated identical requests (deterministic idempotency)
# ---------------------------------------------------------------------------
def test_scenario_repeated_identical_requests():
    """Verify deterministic layout engine produces bit-for-bit identical results on identical requests."""
    payload = {
        "width": 450.0,
        "length": 550.0,
        "furniture": [
            {"id": "bed-1", "name": "Bed", "width": 180.0, "length": 200.0},
            {"id": "nightstand-1", "name": "Nightstand L", "width": 50.0, "length": 50.0},
            {"id": "nightstand-2", "name": "Nightstand R", "width": 50.0, "length": 50.0},
            {"id": "desk-1", "name": "Desk", "width": 140.0, "length": 70.0},
        ],
    }
    res1 = client.post("/layout", json=payload).json()
    res2 = client.post("/layout", json=payload).json()
    res3 = client.post("/layout", json=payload).json()

    assert res1 == res2 == res3
    assert len(res1["placed_items"]) == 4


# ---------------------------------------------------------------------------
# Scenario 11: Integrity Guarantee — Never present an invalid layout as successful
# ---------------------------------------------------------------------------
def test_scenario_no_false_success_layout():
    """Verify that within_bounds is strictly True and overlaps are strictly absent on placed items."""
    payload = {
        "width": 300.0,
        "length": 300.0,
        "furniture": [
            {"id": f"item-{i}", "name": f"Module {i}", "width": 80.0, "length": 80.0}
            for i in range(12)
        ],
    }
    res = client.post("/layout", json=payload)
    data = res.json()

    # All placed items must be within room bounds
    for item in data["placed_items"]:
        assert item["within_bounds"] is True
        assert item["x"] >= 0
        assert item["y"] >= 0
        assert item["x"] + item["width"] <= 300.0 + 1e-4
        assert item["y"] + item["length"] <= 300.0 + 1e-4

    # No placed items can overlap
    rects = [Rect(x=p["x"], y=p["y"], width=p["width"], length=p["length"]) for p in data["placed_items"]]
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            assert not rectangles_overlap(rects[i], rects[j])


# ---------------------------------------------------------------------------
# Scenario 12: AI explanation graceful offline fallback
# ---------------------------------------------------------------------------
def test_scenario_ai_explanation_graceful_offline_fallback():
    """Verify that network exception during AI call returns 200 with status='fallback'."""
    ai_payload = {
        "room_width_cm": 300.0,
        "room_length_cm": 300.0,
        "placed_items": [
            {"id": "f1", "name": "Desk", "placed": True, "x": 0.0, "y": 0.0, "width": 100.0, "length": 60.0}
        ],
        "unplaced_items": [],
    }
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = ConnectionRefusedError("Connection refused")
        with patch("ai._get_env_config") as mock_cfg:
            mock_cfg.return_value = {
                "api_key": "test-key",
                "base_url": "https://api.meta.ai/v1",
                "model": "muse-spark-1.3",
                "mock_mode": False,
            }
            res = client.post("/ai/explain", json=ai_payload)
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "fallback"
            assert "fallback-due-to-network-error" in data["model_used"]
            assert len(data["arrangement_tips"]) > 0
