"""
backend/schemas.py
------------------
Pydantic models for room input validation.

Units: all dimensions are in CENTIMETRES (cm).
Allowed range: 10 cm – 2000 cm per dimension.
"""

from typing import Optional
from pydantic import BaseModel, Field


class FurnitureItem(BaseModel):
    """One piece of furniture to be placed in the room."""
    name: str = Field(..., description="Descriptive name, e.g. 'Sofa' or 'Queen Bed'")
    width: float = Field(..., gt=0, le=2000, description="Width in cm (left-right)")
    length: float = Field(..., gt=0, le=2000, description="Length in cm (front-back)")
    height: float = Field(..., gt=0, le=500, description="Height in cm")


class RoomInput(BaseModel):
    """
    Full room specification submitted by the user.

    - width  : room dimension along the X-axis, in cm.
    - length : room dimension along the Y-axis (depth), in cm.
    - furniture : list of furniture items to arrange; must not be empty.
    - preferences : optional free-form preferences (style, priority items, etc.)
    """
    width: float = Field(..., gt=0, le=2000, description="Room width in cm")
    length: float = Field(..., gt=0, le=2000, description="Room length (depth) in cm")
    furniture: list[FurnitureItem] = Field(
        ..., min_length=1, description="At least one furniture item is required"
    )
    preferences: Optional[dict] = Field(
        default=None,
        description="Optional user preferences, e.g. {'style': 'minimalist', 'priority': 'bed'}"
    )
