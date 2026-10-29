"""
backend/geometry.py
-------------------
Deterministic 2D layout and collision engine for RoomGenius AI.

Coordinate system:
  - Origin (0, 0) is at the top-left corner of the room.
  - X increases to the right: [0, room_width].
  - Y increases downward: [0, room_length].
  - All dimensions and coordinates are in centimetres (cm).

Geometry rules:
  - Axis-Aligned Bounding Boxes (AABB).
  - Touching edges/corners (zero-area overlap) are explicitly allowed.
  - Positive-area overlap between any two furniture items is strictly rejected.
  - Floating-point comparisons use a small tolerance EPSILON.
  - Orientations supported: 0° (standard) and 90° (swapped width/depth).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

EPSILON: float = 1e-4


@dataclass(frozen=True)
class Rect:
    """Axis-aligned rectangle in 2D space."""
    x: float
    y: float
    width: float
    length: float  # depth along Y-axis

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.length


@dataclass
class PlacedItemResult:
    """Result of placing an individual furniture item."""
    id: str
    name: str
    placed: bool
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    length: Optional[float] = None
    height: Optional[float] = None
    rotation: int = 0  # 0 or 90 degrees
    within_bounds: bool = False
    rejection_reason: Optional[str] = None


@dataclass
class LayoutPlanResult:
    """Overall outcome of the deterministic layout generation."""
    feasible: bool
    placed_items: List[PlacedItemResult]
    unplaced_items: List[PlacedItemResult]
    total_furniture: int
    placed_count: int
    unplaced_count: int


def get_oriented_dimensions(width: float, length: float, rotation: int) -> Tuple[float, float]:
    """
    Compute effective (width, depth) for a given rotation.
    - 0°: standard (width, length)
    - 90°: rotated (length, width)
    """
    if rotation == 90:
        return (length, width)
    if rotation == 0:
        return (width, length)
    raise ValueError(f"Unsupported rotation: {rotation}°. Only 0° and 90° are supported.")


def fits_in_boundary(x: float, y: float, width: float, length: float, room_w: float, room_l: float) -> bool:
    """
    Check if a rectangle [x, x+width] x [y, y+length] is completely contained
    within the room boundaries [0, room_w] x [0, room_l].
    """
    if x < -EPSILON or y < -EPSILON:
        return False
    if (x + width) > (room_w + EPSILON):
        return False
    if (y + length) > (room_l + EPSILON):
        return False
    return True


def rectangles_overlap(r1: Rect, r2: Rect) -> bool:
    """
    Check if two rectangles have positive-area overlap.
    Touching edges/corners (where intersection width or height <= EPSILON) are allowed.
    """
    overlap_x = min(r1.right, r2.right) - max(r1.x, r2.x)
    overlap_y = min(r1.bottom, r2.bottom) - max(r1.y, r2.y)

    return (overlap_x > EPSILON) and (overlap_y > EPSILON)


def can_fit_in_room_any_orientation(item_w: float, item_l: float, room_w: float, room_l: float) -> bool:
    """Check if an item can fit within the room in at least one supported orientation."""
    for rot in (0, 90):
        w, l = get_oriented_dimensions(item_w, item_l, rot)
        if w <= (room_w + EPSILON) and l <= (room_l + EPSILON):
            return True
    return False


def generate_candidate_points(placed: List[Rect], room_w: float, room_l: float) -> List[Tuple[float, float]]:
    """
    Generate deterministic candidate anchor points (top-left corners) for placing the next item.
    Starts at origin (0, 0), plus edges and corners of existing placed items.
    Candidate points are sorted by (y asc, x asc) to favor compact top-left packing.
    """
    points = {(0.0, 0.0)}

    for r in placed:
        # Align along right edge
        points.add((round(r.right, 4), round(r.y, 4)))
        points.add((round(r.right, 4), 0.0))
        # Align along bottom edge
        points.add((round(r.x, 4), round(r.bottom, 4)))
        points.add((0.0, round(r.bottom, 4)))
        # Corner of placed rectangle
        points.add((round(r.right, 4), round(r.bottom, 4)))

    # Filter out points clearly outside room boundaries
    valid_points = [
        (x, y) for (x, y) in points
        if 0.0 <= x <= (room_w + EPSILON) and 0.0 <= y <= (room_l + EPSILON)
    ]

    # Deterministic order: top-to-bottom, left-to-right
    valid_points.sort(key=lambda pt: (pt[1], pt[0]))
    return valid_points


def generate_layout(
    room_width: float,
    room_length: float,
    furniture_items: list,
) -> LayoutPlanResult:
    """
    Deterministic layout generation.
    1. Sort furniture by footprint area descending with stable tie-breaker (id).
    2. Sequentially place items at the first valid candidate anchor point and orientation.
    3. Return structured placement and rejection records.
    """
    # Defensive dimension checks
    if room_width <= 0 or room_length <= 0:
        raise ValueError("Room dimensions must be strictly positive numbers.")

    # Stable deterministic sort: footprint area descending, then id ascending
    sorted_items = sorted(
        furniture_items,
        key=lambda item: (-(item.width * item.length), item.id),
    )

    placed_rects: List[Rect] = []
    placed_results: List[PlacedItemResult] = []
    unplaced_results: List[PlacedItemResult] = []

    for item in sorted_items:
        # Check if item is fundamentally larger than the room in all orientations
        if not can_fit_in_room_any_orientation(item.width, item.length, room_width, room_length):
            unplaced_results.append(
                PlacedItemResult(
                    id=item.id,
                    name=item.name,
                    placed=False,
                    width=item.width,
                    length=item.length,
                    height=item.height,
                    rejection_reason="Item dimensions exceed room boundaries in all supported orientations (0°, 90°).",
                )
            )
            continue

        candidate_points = generate_candidate_points(placed_rects, room_width, room_length)
        placed_this_item = False

        # Try orientations: 0° first, then 90°
        for rot in (0, 90):
            eff_w, eff_l = get_oriented_dimensions(item.width, item.length, rot)

            for cx, cy in candidate_points:
                # 1. Room boundary check
                if not fits_in_boundary(cx, cy, eff_w, eff_l, room_width, room_length):
                    continue

                candidate_rect = Rect(x=cx, y=cy, width=eff_w, length=eff_l)

                # 2. Collision check against already placed items
                has_collision = any(
                    rectangles_overlap(candidate_rect, existing)
                    for existing in placed_rects
                )

                if not has_collision:
                    # Valid placement found!
                    placed_rects.append(candidate_rect)
                    placed_results.append(
                        PlacedItemResult(
                            id=item.id,
                            name=item.name,
                            placed=True,
                            x=round(cx, 2),
                            y=round(cy, 2),
                            width=round(eff_w, 2),
                            length=round(eff_l, 2),
                            height=item.height,
                            rotation=rot,
                            within_bounds=True,
                            rejection_reason=None,
                        )
                    )
                    placed_this_item = True
                    break

            if placed_this_item:
                break

        if not placed_this_item:
            unplaced_results.append(
                PlacedItemResult(
                    id=item.id,
                    name=item.name,
                    placed=False,
                    width=item.width,
                    length=item.length,
                    height=item.height,
                    rejection_reason="No collision-free candidate position found within room boundaries.",
                )
            )

    total = len(furniture_items)
    placed_cnt = len(placed_results)
    unplaced_cnt = len(unplaced_results)

    return LayoutPlanResult(
        feasible=(unplaced_cnt == 0),
        placed_items=placed_results,
        unplaced_items=unplaced_results,
        total_furniture=total,
        placed_count=placed_cnt,
        unplaced_count=unplaced_cnt,
    )

