"""
backend/test_geometry.py
------------------------
Unit tests for deterministic 2D geometry and layout placement engine.
"""

from dataclasses import dataclass
import pytest
from geometry import (
    Rect,
    fits_in_boundary,
    generate_layout,
    get_oriented_dimensions,
    rectangles_overlap,
)


@dataclass
class MockItem:
    id: str
    name: str
    width: float
    length: float
    height: float = 80.0


# ── 1. Orientation & Boundary Checks ──────────────────────────────────

def test_rotation_swaps_dimensions():
    """0° preserves dimensions, 90° swaps width and depth."""
    w, l = get_oriented_dimensions(100.0, 50.0, 0)
    assert w == 100.0 and l == 50.0

    w_rot, l_rot = get_oriented_dimensions(100.0, 50.0, 90)
    assert w_rot == 50.0 and l_rot == 100.0


def test_unsupported_rotation_raises():
    """Only 0° and 90° are supported."""
    with pytest.raises(ValueError, match="Unsupported rotation: 45°"):
        get_oriented_dimensions(100.0, 50.0, 45)


def test_fits_in_boundary():
    """Checks inside, outside, and exactly at boundary."""
    # Fully inside
    assert fits_in_boundary(0, 0, 100, 100, 400, 500) is True
    # Exactly on boundary
    assert fits_in_boundary(300, 400, 100, 100, 400, 500) is True
    # Exceeding right edge
    assert fits_in_boundary(301, 0, 100, 100, 400, 500) is False
    # Exceeding bottom edge
    assert fits_in_boundary(0, 401, 100, 100, 400, 500) is False
    # Negative coordinates
    assert fits_in_boundary(-1, 0, 100, 100, 400, 500) is False


# ── 2. Collision & Overlap Rules ──────────────────────────────────────

def test_overlapping_rectangles_detected():
    """Positive area overlap must return True."""
    r1 = Rect(x=0, y=0, width=100, length=100)
    r2 = Rect(x=50, y=50, width=100, length=100)
    assert rectangles_overlap(r1, r2) is True
    assert rectangles_overlap(r2, r1) is True


def test_touching_edges_allowed():
    """Touching along an edge (zero-area intersection) is NOT an overlap."""
    r1 = Rect(x=0, y=0, width=100, length=100)
    r2 = Rect(x=100, y=0, width=100, length=100)  # touches at x=100
    assert rectangles_overlap(r1, r2) is False

    r3 = Rect(x=0, y=100, width=100, length=100)  # touches at y=100
    assert rectangles_overlap(r1, r3) is False


def test_touching_corner_allowed():
    """Touching only at a single vertex is NOT an overlap."""
    r1 = Rect(x=0, y=0, width=100, length=100)
    r2 = Rect(x=100, y=100, width=100, length=100)  # touches at (100, 100)
    assert rectangles_overlap(r1, r2) is False


def test_disjoint_rectangles():
    """Completely separated rectangles do not overlap."""
    r1 = Rect(x=0, y=0, width=100, length=100)
    r2 = Rect(x=200, y=200, width=100, length=100)
    assert rectangles_overlap(r1, r2) is False


# ── 3. Deterministic Layout Generation ────────────────────────────────

def test_single_item_placement():
    """A single item should be placed at the room origin (0, 0)."""
    items = [MockItem(id="sofa-1", name="Sofa", width=200, length=90)]
    res = generate_layout(room_width=400, room_length=500, furniture_items=items)

    assert res.feasible is True
    assert res.placed_count == 1
    assert res.unplaced_count == 0
    placed = res.placed_items[0]
    assert placed.id == "sofa-1"
    assert placed.x == 0.0
    assert placed.y == 0.0
    assert placed.within_bounds is True


def test_multiple_items_placement_no_overlap():
    """Multiple items should be placed with 0 collisions and within bounds."""
    items = [
        MockItem(id="bed-1", name="Queen Bed", width=160, length=200),
        MockItem(id="desk-1", name="Study Desk", width=120, length=60),
        MockItem(id="wardrobe-1", name="Wardrobe", width=100, length=60),
    ]
    res = generate_layout(room_width=400, room_length=400, furniture_items=items)

    assert res.feasible is True
    assert res.placed_count == 3
    assert res.unplaced_count == 0

    # Verify pairwise non-overlap for all placed items
    rects = [
        Rect(x=p.x, y=p.y, width=p.width, length=p.length)
        for p in res.placed_items
    ]
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            assert rectangles_overlap(rects[i], rects[j]) is False, f"{res.placed_items[i].id} overlaps with {res.placed_items[j].id}"


def test_item_larger_than_room_rejected():
    """An item larger than the room in all orientations is rejected with a clear message."""
    items = [MockItem(id="huge-table", name="Conference Table", width=500, length=600)]
    res = generate_layout(room_width=400, room_length=400, furniture_items=items)

    assert res.feasible is False
    assert res.placed_count == 0
    assert res.unplaced_count == 1
    unplaced = res.unplaced_items[0]
    assert unplaced.id == "huge-table"
    assert unplaced.placed is False
    assert "exceed room boundaries in all supported orientations" in unplaced.rejection_reason


def test_item_fits_only_with_rotation():
    """An item that only fits when rotated 90° should be rotated."""
    # Room is 300 wide x 150 deep. Item is 120 wide x 250 deep (exceeds depth at 0°, fits at 90°)
    items = [MockItem(id="bench-1", name="Long Bench", width=120, length=250)]
    res = generate_layout(room_width=300, room_length=150, furniture_items=items)

    assert res.feasible is True
    assert res.placed_count == 1
    placed = res.placed_items[0]
    assert placed.rotation == 90
    assert placed.width == 250.0  # swapped
    assert placed.length == 120.0  # swapped
    assert fits_in_boundary(placed.x, placed.y, placed.width, placed.length, 300, 150)


def test_partial_placement_when_room_crowded():
    """When items cannot all fit, the engine places what fits and reports unplaced ones."""
    # Room is 200 x 200 (area 40,000). Three items of 150x150 (area 22,500 each)
    items = [
        MockItem(id="box-1", name="Big Box 1", width=150, length=150),
        MockItem(id="box-2", name="Big Box 2", width=150, length=150),
        MockItem(id="box-3", name="Big Box 3", width=150, length=150),
    ]
    res = generate_layout(room_width=200, room_length=200, furniture_items=items)

    assert res.feasible is False
    assert res.placed_count == 1
    assert res.unplaced_count == 2
    for unp in res.unplaced_items:
        assert unp.placed is False
        assert "No collision-free candidate position found" in unp.rejection_reason


def test_layout_is_deterministic():
    """Calling generate_layout repeatedly with the same items produces identical placements."""
    items = [
        MockItem(id="chair-b", name="Chair B", width=60, length=60),
        MockItem(id="table-a", name="Table A", width=120, length=80),
        MockItem(id="chair-a", name="Chair A", width=60, length=60),
    ]

    res1 = generate_layout(room_width=400, room_length=400, furniture_items=items)
    res2 = generate_layout(room_width=400, room_length=400, furniture_items=items)

    assert res1.feasible == res2.feasible
    assert res1.placed_count == res2.placed_count

    for p1, p2 in zip(res1.placed_items, res2.placed_items):
        assert p1.id == p2.id
        assert p1.x == p2.x
        assert p1.y == p2.y
        assert p1.width == p2.width
        assert p1.length == p2.length
        assert p1.rotation == p2.rotation


def test_invalid_room_dimension_raises():
    """Zero or negative room dimensions raise ValueError."""
    with pytest.raises(ValueError, match="Room dimensions must be strictly positive"):
        generate_layout(room_width=0, room_length=400, furniture_items=[])

