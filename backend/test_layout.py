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
    """A well-formed payload returns 200 with status 'accepted'."""
    res = client.post("/layout", json=VALID_PAYLOAD)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "accepted"
    assert body["summary"]["room_width_cm"] == 400
    assert body["summary"]["room_length_cm"] == 500
    assert body["summary"]["furniture_count"] == 2
    assert body["summary"]["has_preferences"] is True


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


# ── 6. Health endpoint still works ──────────────────────────────────

def test_health_endpoint():
    """GET /health returns 200."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy"}
