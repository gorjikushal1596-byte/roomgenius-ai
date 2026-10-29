"""
backend/test_layout.py
----------------------
Tests for POST /layout endpoint and Pydantic schema validation.

Run:  cd backend && .venv/Scripts/python -m pytest test_layout.py -v
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

# ── Helpers ──────────────────────────────────────────────────────────

VALID_FURNITURE = [
    {"id": "sofa-1", "name": "Sofa", "width": 200, "length": 90},
    {"id": "table-1", "name": "Coffee Table", "width": 120, "length": 60, "height": 45},
]

VALID_PAYLOAD = {
    "width": 400,
    "length": 500,
    "furniture": VALID_FURNITURE,
    "preferences": {"style": "minimalist"},
}


# ── 1. Valid submissions ─────────────────────────────────────────────

def test_valid_room_with_furniture():
    """A well-formed payload returns 200 with status 'accepted' and placed items."""
    res = client.post("/layout", json=VALID_PAYLOAD)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "accepted"
    assert body["feasible"] is True
    assert body["summary"]["room_width_cm"] == 400
    assert body["summary"]["room_length_cm"] == 500
    assert body["summary"]["furniture_count"] == 2
    assert body["summary"]["placed_count"] == 2
    assert body["summary"]["unplaced_count"] == 0
    assert body["summary"]["has_preferences"] is True
    assert len(body["placed_items"]) == 2
    assert len(body["unplaced_items"]) == 0

    first_item = body["placed_items"][0]
    assert first_item["placed"] is True
    assert first_item["x"] is not None
    assert first_item["y"] is not None
    assert first_item["rotation"] in (0, 90)
    assert first_item["within_bounds"] is True


def test_layout_api_unplaced_item_reported():
    """When an item is too large for the room, API returns feasible=False and unplaced details."""
    payload = {
        "width": 200,
        "length": 200,
        "furniture": [
            {"id": "huge-1", "name": "Giant Desk", "width": 500, "length": 500}
        ],
    }
    res = client.post("/layout", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["feasible"] is False
    assert body["summary"]["placed_count"] == 0
    assert body["summary"]["unplaced_count"] == 1
    assert len(body["unplaced_items"]) == 1
    unplaced = body["unplaced_items"][0]
    assert unplaced["placed"] is False
    assert "exceed room boundaries" in unplaced["rejection_reason"]


def test_valid_room_empty_furniture():
    """Empty furniture list is accepted (user may add later)."""
    payload = {"width": 300, "length": 400}
    res = client.post("/layout", json=payload)
    assert res.status_code == 200
    assert res.json()["summary"]["furniture_count"] == 0


def test_valid_room_with_height():
    """Optional room height is accepted and echoed back."""
    payload = {"width": 300, "length": 400, "height": 280}
    res = client.post("/layout", json=payload)
    assert res.status_code == 200
    assert res.json()["summary"]["room_height_cm"] == 280


# ── 2. Missing room dimensions ──────────────────────────────────────

def test_missing_width():
    """Missing room width returns 422."""
    res = client.post("/layout", json={"length": 400})
    assert res.status_code == 422


def test_missing_length():
    """Missing room length returns 422."""
    res = client.post("/layout", json={"width": 300})
    assert res.status_code == 422


def test_missing_both_dimensions():
    """Missing both dimensions returns 422."""
    res = client.post("/layout", json={})
    assert res.status_code == 422


# ── 3. Zero or negative dimensions ──────────────────────────────────

def test_zero_room_width():
    """Zero width is rejected."""
    res = client.post("/layout", json={"width": 0, "length": 400})
    assert res.status_code == 422


def test_negative_room_length():
    """Negative length is rejected."""
    res = client.post("/layout", json={"width": 300, "length": -50})
    assert res.status_code == 422


def test_zero_furniture_width():
    """Furniture with zero width is rejected."""
    payload = {
        "width": 300,
        "length": 400,
        "furniture": [{"id": "f1", "name": "Desk", "width": 0, "length": 60}],
    }
    res = client.post("/layout", json=payload)
    assert res.status_code == 422


def test_negative_furniture_length():
    """Furniture with negative length is rejected."""
    payload = {
        "width": 300,
        "length": 400,
        "furniture": [{"id": "f1", "name": "Desk", "width": 120, "length": -10}],
    }
    res = client.post("/layout", json=payload)
    assert res.status_code == 422


# ── 4. Invalid numeric input ────────────────────────────────────────

def test_non_numeric_width():
    """Non-numeric width is rejected."""
    res = client.post("/layout", json={"width": "abc", "length": 400})
    assert res.status_code == 422


def test_infinity_width():
    """Infinity is not valid JSON — even if hand-crafted, Pydantic rejects it."""
    res = client.post(
        "/layout",
        content='{"width": 999999, "length": 400}',
        headers={"Content-Type": "application/json"},
    )
    # 999999 > le=2000, so Pydantic rejects it
    assert res.status_code == 422


def test_non_finite_width_string():
    """A string like 'Infinity' for a numeric field is rejected."""
    res = client.post(
        "/layout",
        content='{"width": "Infinity", "length": 400}',
        headers={"Content-Type": "application/json"},
    )
    assert res.status_code == 422


def test_invalid_unit():
    """Units other than 'cm' are rejected."""
    payload = {"width": 300, "length": 400, "unit": "inch"}
    res = client.post("/layout", json=payload)
    assert res.status_code == 422


def test_valid_unit_explicit():
    """Explicitly passing unit='cm' is accepted."""
    payload = {"width": 300, "length": 400, "unit": "cm"}
    res = client.post("/layout", json=payload)
    assert res.status_code == 200
    assert res.json()["summary"]["unit"] == "cm"


# ── 5. Furniture item validation ────────────────────────────────────

def test_furniture_missing_name():
    """Furniture without a name is rejected."""
    payload = {
        "width": 300,
        "length": 400,
        "furniture": [{"id": "f1", "width": 120, "length": 60}],
    }
    res = client.post("/layout", json=payload)
    assert res.status_code == 422


def test_furniture_whitespace_name():
    """Furniture with whitespace-only name is rejected."""
    payload = {
        "width": 300,
        "length": 400,
        "furniture": [{"id": "f1", "name": "   ", "width": 120, "length": 60}],
    }
    res = client.post("/layout", json=payload)
    assert res.status_code == 422


def test_furniture_missing_id():
    """Furniture without an id is rejected."""
    payload = {
        "width": 300,
        "length": 400,
        "furniture": [{"name": "Desk", "width": 120, "length": 60}],
    }
    res = client.post("/layout", json=payload)
    assert res.status_code == 422


def test_duplicate_furniture_id():
    """Furniture items with duplicate IDs are rejected."""
    payload = {
        "width": 300,
        "length": 400,
        "furniture": [
            {"id": "chair-1", "name": "Chair 1", "width": 50, "length": 50},
            {"id": "chair-1", "name": "Chair 2", "width": 50, "length": 50},
        ],
    }
    res = client.post("/layout", json=payload)
    assert res.status_code == 422


def test_exceeds_max_dimension():
    """Room dimension exceeding 2000 cm is rejected."""
    res = client.post("/layout", json={"width": 2001, "length": 400})
    assert res.status_code == 422


def test_exceeds_max_furniture_count():
    """Submitting more than 100 furniture items is rejected with 422."""
    items = [
        {"id": f"chair-{i}", "name": f"Chair {i}", "width": 50, "length": 50}
        for i in range(101)
    ]
    payload = {"width": 1000, "length": 1000, "furniture": items}
    res = client.post("/layout", json=payload)
    assert res.status_code == 422


def test_layout_api_rotation_applied():
    """API successfully rotates item 90 degrees when it only fits rotated."""
    payload = {
        "width": 300,
        "length": 200,
        "furniture": [
            {"id": "bench-1", "name": "Long Bench", "width": 100, "length": 250}
        ],
    }
    res = client.post("/layout", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["feasible"] is True
    placed = body["placed_items"][0]
    assert placed["rotation"] == 90
    assert placed["width"] == 250
    assert placed["length"] == 100
    assert placed["within_bounds"] is True


def test_layout_api_multiple_items_no_overlap():
    """API places multiple items without positive-area overlap."""
    payload = {
        "width": 500,
        "length": 500,
        "furniture": [
            {"id": "bed-1", "name": "King Bed", "width": 180, "length": 200},
            {"id": "desk-1", "name": "Work Desk", "width": 140, "length": 70},
            {"id": "wardrobe-1", "name": "Wardrobe", "width": 120, "length": 60},
            {"id": "chair-1", "name": "Office Chair", "width": 60, "length": 60},
        ],
    }
    res = client.post("/layout", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["feasible"] is True
    assert len(body["placed_items"]) == 4

    items = body["placed_items"]
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i], items[j]
            overlap_x = min(a["x"] + a["width"], b["x"] + b["width"]) - max(a["x"], b["x"])
            overlap_y = min(a["y"] + a["length"], b["y"] + b["length"]) - max(a["y"], b["y"])
            assert not (overlap_x > 1e-4 and overlap_y > 1e-4), f"Items {a['id']} and {b['id']} overlap!"


# ── 6. Health endpoint still works ──────────────────────────────────

def test_health_endpoint():
    """GET /health returns 200."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy"}
