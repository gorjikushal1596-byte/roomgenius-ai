"""
backend/schemas.py
------------------
Pydantic models for room input validation.

Units: all dimensions are in CENTIMETRES (cm).
"""

from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class FurnitureItem(BaseModel):
    """One piece of furniture to be placed in the room."""
    id: str = Field(..., min_length=1, description="Stable unique identifier, e.g. 'chair-1'")
    name: str = Field(..., min_length=1, description="Descriptive name, e.g. 'Sofa' or 'Queen Bed'")
    width: float = Field(..., gt=0, le=2000, description="Width in cm (left-right)")
    length: float = Field(..., gt=0, le=2000, description="Depth in cm (front-back)")
    height: Optional[float] = Field(None, gt=0, le=500, description="Height in cm (optional)")

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Furniture name cannot be blank or whitespace-only")
        return trimmed


class RoomInput(BaseModel):
    """
    Full room specification submitted by the user.

    - width  : room dimension along the X-axis, in cm.
    - length : room dimension along the Y-axis (depth), in cm.
    - height : optional room ceiling height, in cm.
    - unit   : measurement unit label (always 'cm' for now).
    - furniture : list of furniture items to arrange (can be empty).
    - preferences : optional structured preferences.
    """
    width: float = Field(..., gt=0, le=2000, description="Room width in cm")
    length: float = Field(..., gt=0, le=2000, description="Room length (depth) in cm")
    height: Optional[float] = Field(None, gt=0, le=500, description="Room ceiling height in cm (optional)")
    unit: Literal["cm"] = Field(default="cm", description="Measurement unit (strictly 'cm')")
    furniture: list[FurnitureItem] = Field(
        default_factory=list,
        max_length=100,
        description="List of furniture items (can be empty, max 100 items)",
    )

    @field_validator("furniture")
    @classmethod
    def validate_unique_furniture_ids(cls, items: list[FurnitureItem]) -> list[FurnitureItem]:
        seen = set()
        for item in items:
            if item.id in seen:
                raise ValueError(f"Duplicate furniture id: '{item.id}'")
            seen.add(item.id)
        return items
    preferences: Optional[dict] = Field(
        default=None,
        description="Optional user preferences, e.g. {'style': 'minimalist', 'priority': 'bed'}"
    )


class PlacedFurnitureItem(BaseModel):
    """Details of a placed or evaluated furniture item."""
    id: str
    name: str
    placed: bool
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    length: Optional[float] = None
    height: Optional[float] = None
    rotation: int = 0
    within_bounds: bool = False
    rejection_reason: Optional[str] = None


class LayoutResponse(BaseModel):
    """API response contract for POST /layout."""
    status: str = "accepted"
    feasible: bool
    summary: dict
    placed_items: list[PlacedFurnitureItem] = Field(default_factory=list)
    unplaced_items: list[PlacedFurnitureItem] = Field(default_factory=list)


class LayoutPreferences(BaseModel):
    """Structured, bounded user design preferences."""
    style: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Aesthetic style name")
    priority: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Placement priority or item")
    focus: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Design focus area")
    vibe: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Atmospheric vibe")
    lighting: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Lighting preference")


class LayoutExplanationRequest(BaseModel):
    """Request payload to generate an AI explanation for an existing layout."""
    room_width_cm: float = Field(..., gt=0, le=2000, description="Room width in cm")
    room_length_cm: float = Field(..., gt=0, le=2000, description="Room length in cm")
    room_height_cm: Optional[float] = Field(None, gt=0, le=500, description="Room height in cm")
    preferences: Optional[LayoutPreferences] = Field(default=None, description="User design preferences")
    placed_items: list[PlacedFurnitureItem] = Field(
        default_factory=list,
        max_length=100,
        description="Items placed by deterministic engine (max 100)",
    )
    unplaced_items: list[PlacedFurnitureItem] = Field(
        default_factory=list,
        max_length=100,
        description="Items rejected by deterministic engine (max 100)",
    )



class LayoutExplanationResponse(BaseModel):
    """Structured AI explanation grounded in deterministic layout facts."""
    status: Literal["success", "fallback"] = "success"
    summary: str = Field(..., description="High-level architectural summary of the layout")
    design_reasoning: str = Field(..., description="Why this arrangement optimizes aesthetics and functionality")
    arrangement_tips: list[str] = Field(default_factory=list, description="Step-by-step physical placement guidance")
    trade_offs: list[str] = Field(default_factory=list, description="Space trade-offs or clearance notices")
    model_used: str = Field(default="mock-model", description="Model identifier used for generation")
    reasoning_content: Optional[str] = Field(default=None, description="Model internal reasoning trace if available")

