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
        default_factory=list, description="List of furniture items (can be empty)"
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
