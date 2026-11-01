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
    id: str = Field(..., min_length=1, max_length=100, description="Stable unique identifier, e.g. 'chair-1'")
    name: str = Field(..., min_length=1, max_length=200, description="Descriptive name, e.g. 'Sofa' or 'Queen Bed'")
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
    id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    placed: bool
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    length: Optional[float] = None
    height: Optional[float] = None
    rotation: int = 0
    within_bounds: bool = False
    rejection_reason: Optional[str] = Field(default=None, max_length=300)


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


# ── Meta SAM 3.1 & Muse Image Schemas ───────────────────────────────


class NormalizedBoundingBox(BaseModel):
    """Normalized 2D bounding box coordinates relative to image width and height [0.0, 1.0]."""
    ymin: float = Field(..., ge=0.0, le=1.0, description="Top normalized coordinate")
    xmin: float = Field(..., ge=0.0, le=1.0, description="Left normalized coordinate")
    ymax: float = Field(..., ge=0.0, le=1.0, description="Bottom normalized coordinate")
    xmax: float = Field(..., ge=0.0, le=1.0, description="Right normalized coordinate")

    @field_validator("ymax")
    @classmethod
    def validate_vertical_span(cls, v: float, info) -> float:
        ymin = info.data.get("ymin", 0.0)
        if v < ymin:
            raise ValueError("ymax cannot be less than ymin")
        return v

    @field_validator("xmax")
    @classmethod
    def validate_horizontal_span(cls, v: float, info) -> float:
        xmin = info.data.get("xmin", 0.0)
        if v < xmin:
            raise ValueError("xmax cannot be less than xmin")
        return v


class DetectedObject(BaseModel):
    """A furniture or room object detected by SAM 3.1 segmentation."""
    id: str = Field(..., min_length=1, max_length=100, description="Temporary identifier for detected entity")
    label: str = Field(..., min_length=1, max_length=100, description="Detected object label, e.g. 'bed' or 'desk'")
    category: Literal["sleeping", "seating", "work", "storage", "other"] = Field(
        default="other",
        description="Standardized room furniture category",
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    box: NormalizedBoundingBox = Field(..., description="Normalized 2D bounding box on image")
    suggested_width_cm: Optional[float] = Field(None, gt=0, le=2000, description="User-calibrated width in cm")
    suggested_length_cm: Optional[float] = Field(None, gt=0, le=2000, description="User-calibrated depth in cm")
    calibrated: bool = Field(
        default=False,
        description="Whether a human user has calibrated/confirmed metric dimensions",
    )


class ImageSegmentationRequest(BaseModel):
    """JSON payload containing base64 encoded image data for SAM 3.1 segmentation."""
    image_base64: str = Field(..., description="Base64 encoded image string or Data URI")
    filename: Optional[str] = Field(default="room_photo.jpg", max_length=100, description="Original filename")
    mime_type: Optional[str] = Field(default="image/jpeg", max_length=50, description="Image MIME type")


class SegmentationResponse(BaseModel):
    """Structured response from SAM 3.1 furniture segmentation."""
    status: Literal["success", "fallback", "error"] = "success"
    image_filename: str = Field(..., max_length=255, description="Sanitized original image filename")
    objects_detected: list[DetectedObject] = Field(
        default_factory=list,
        max_length=50,
        description="List of detected furniture items",
    )
    total_detected: int = Field(default=0, ge=0, description="Total count of detected items")
    model_used: str = Field(default="sam-3.1", description="Model or mock provider identifier")
    message: str = Field(default="", max_length=500, description="Informational message or error summary")
    requires_user_calibration: bool = Field(
        default=True,
        description="Golden Rule: Pixel detections must be calibrated by the user before placement",
    )


class ImagePreviewRequest(BaseModel):
    """Payload to request an AI visual preview from Meta Muse Image."""
    room_width_cm: float = Field(..., gt=0, le=2000, description="Room width in cm")
    room_length_cm: float = Field(..., gt=0, le=2000, description="Room length in cm")
    style: str = Field(
        default="modern",
        min_length=1,
        max_length=50,
        description="Target interior design aesthetic, e.g. 'minimalist'",
    )
    placed_items: list[PlacedFurnitureItem] = Field(
        default_factory=list,
        max_length=50,
        description="Placed items with deterministic coordinates to guide visual composition",
    )
    custom_prompt_additions: Optional[str] = Field(
        default=None,
        max_length=300,
        description="Optional user design notes (materials, lighting, colors)",
    )


class ImagePreviewResponse(BaseModel):
    """Visual preview output generated by Meta Muse Image."""
    status: Literal["success", "fallback"] = "success"
    image_data: str = Field(..., description="Base64 Data URI or image URL")
    format: Literal["url", "b64_json", "svg_data_uri"] = "b64_json"
    prompt_used: str = Field(..., description="Constructed architectural prompt sent to the model")
    model_used: str = Field(default="muse-image-1.0", description="Model identifier used for generation")
    disclaimer: str = Field(
        default="Aesthetic concept preview only. Refer to 2D Floorplan for precise physical dimensions and clearances.",
        description="Truthful disclosure preventing confusion between artistic render and deterministic layout",
    )


# ── Depth Anything V2 Schemas ──────────────────────────────────────


class ObjectDepthProfile(BaseModel):
    """Estimated relative/metric depth characteristics for a detected furniture item."""
    item_id: str = Field(..., min_length=1, max_length=100)
    label: str = Field(..., min_length=1, max_length=100)
    median_depth_m: float = Field(..., ge=0.0, le=20.0, description="Estimated distance from camera in meters")
    relative_layer: Literal["foreground", "midground", "background"] = Field(
        ...,
        description="Spatial depth layer categorizing proximity along camera axis",
    )
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class DepthEstimationRequest(BaseModel):
    """Payload to request depth map estimation for a room photo."""
    image_base64: str = Field(..., description="Base64 encoded image string or Data URI")
    filename: Optional[str] = Field(default="room.jpg", max_length=100)
    calibrated_room_length_cm: Optional[float] = Field(
        None,
        gt=0,
        le=2000,
        description="User-confirmed room depth in cm used to calibrate absolute scale",
    )
    detected_boxes: list[NormalizedBoundingBox] = Field(
        default_factory=list,
        max_length=50,
        description="Optional list of SAM-detected bounding boxes to sample depth per object",
    )


class DepthEstimationResponse(BaseModel):
    """Structured response from Depth Anything V2 service."""
    status: Literal["success", "fallback", "error"] = "success"
    depth_map_data: str = Field(..., description="Base64 Data URI containing depth heatmap/colormap visualization")
    min_depth_m: float = Field(default=0.5, ge=0.0, description="Closest estimated point in meters")
    max_depth_m: float = Field(default=5.0, ge=0.0, le=20.0, description="Furthest estimated point in meters")
    object_depth_profiles: list[ObjectDepthProfile] = Field(
        default_factory=list,
        description="Depth layering profiles mapped across detected furniture items",
    )
    processing_time_ms: float = Field(..., ge=0.0, description="Inference or simulation latency in milliseconds")
    model_used: str = Field(
        default="Depth-Anything-V2-Metric-Indoor-Small",
        description="Model identifier or mock provider",
    )
    disclaimer: str = Field(
        default="Monocular depth estimates provide relative spatial ordering and must not replace physical room measurements.",
        description="Truthful disclosure preventing confusion between optical depth and certified physical geometry",
    )



