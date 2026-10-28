"""
backend/schemas.py
------------------
Pydantic models for room input validation.

Units: all dimensions are in CENTIMETRES (cm).
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class FurnitureItem(BaseModel):
    """One piece of furniture to be placed in the room."""
    id: str = Field(..., min_length=1, description="Stable unique identifier, e.g. 'chair-1'")
    name: str = Field(..., min_length=1, description="Descriptive name, e.g. 'Sofa' or 'Queen Bed'")
    width: float = Field(..., gt=0, le=2000, description="Width in cm (left-right)")
    length: float = Field(..., gt=0, le=2000, description="Depth in cm (front-back)")
    height: Optional[float] = Field(None, gt=0, le=500, description="Height in cm (optional)")


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
    unit: str = Field(default="cm", description="Measurement unit (always 'cm')")
    furniture: list[FurnitureItem] = Field(
        default_factory=list, description="List of furniture items (can be empty)"
    )
    preferences: Optional[dict] = Field(
        default=None,
        description="Optional user preferences, e.g. {'style': 'minimalist', 'priority': 'bed'}"
    )
