"""
backend/main.py
---------------
RoomGenius AI — FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import base64
import threading

from geometry import generate_layout
from ai import generate_layout_explanation, generate_mock_explanation, is_ai_configured
from sam_service import segment_furniture_image, generate_mock_segmentation, is_sam_configured
from muse_image_service import generate_interior_preview, generate_mock_preview, is_muse_image_configured
from depth_service import estimate_room_depth, generate_mock_depth_map, is_depth_configured
from schemas import (
    DepthEstimationRequest,
    DepthEstimationResponse,
    ImagePreviewRequest,
    ImagePreviewResponse,
    ImageSegmentationRequest,
    LayoutExplanationRequest,
    LayoutExplanationResponse,
    LayoutResponse,
    RoomInput,
    SegmentationResponse,
)

app = FastAPI(
    title="RoomGenius AI",
    description="AI-powered room layout assistant — backend API",
    version="0.3.0",
)

# Allow Vite dev server (port 5173) and preview server (port 4173) to call the API during development.
# In production this should be replaced with the actual domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
def health_check():
    """Simple liveness probe — returns 200 when the server is up."""
    return {"status": "healthy"}


@app.post("/layout", response_model=LayoutResponse, tags=["room"])
def submit_layout(room: RoomInput):
    """
    Accept, validate, and compute a deterministic furniture layout.

    Uses deterministic AABB candidate-anchor placement and collision checking.
    Returns placement coordinates (x, y), effective dimensions, orientation (0° or 90°),
    and per-item rejection details if unplaceable.
    """
    plan = generate_layout(
        room_width=room.width,
        room_length=room.length,
        furniture_items=room.furniture,
    )

    return {
        "status": "accepted",
        "feasible": plan.feasible,
        "summary": {
            "room_width_cm": room.width,
            "room_length_cm": room.length,
            "room_height_cm": room.height,
            "unit": room.unit,
            "furniture_count": plan.total_furniture,
            "placed_count": plan.placed_count,
            "unplaced_count": plan.unplaced_count,
            "has_preferences": room.preferences is not None,
        },
        "placed_items": [item.__dict__ for item in plan.placed_items],
        "unplaced_items": [item.__dict__ for item in plan.unplaced_items],
    }


@app.get("/ai/status", tags=["ai"])
def get_ai_status():
    """Check whether Meta Model API is configured with credentials."""
    return {"configured": is_ai_configured()}


@app.get("/ai/models-status", tags=["ai"])
def get_models_status():
    """Check configuration and availability status across all integrated Meta AI models."""
    return {
        "muse_spark": is_ai_configured(),
        "sam_3_1": is_sam_configured(),
        "muse_image": is_muse_image_configured(),
        "depth_anything_v2": is_depth_configured(),
    }


# Concurrency limiters to protect worker threads and API credit limits
AI_CONCURRENCY_LIMIT = 2
_ai_semaphore = threading.BoundedSemaphore(value=AI_CONCURRENCY_LIMIT)
_sam_semaphore = threading.BoundedSemaphore(value=1)
_muse_image_semaphore = threading.BoundedSemaphore(value=1)
_depth_semaphore = threading.BoundedSemaphore(value=1)


def _extract_image_bytes(data_str: str) -> tuple[bytes, str]:
    """Parse raw base64 or Data URI string into raw bytes and detected MIME type."""
    cleaned = data_str.strip()
    if "," in cleaned and "base64" in cleaned:
        header, encoded = cleaned.split(",", 1)
        mime = "image/jpeg"
        if "image/png" in header:
            mime = "image/png"
        elif "image/webp" in header:
            mime = "image/webp"
        return base64.b64decode(encoded), mime

    return base64.b64decode(cleaned), "image/jpeg"


@app.post("/ai/explain", response_model=LayoutExplanationResponse, tags=["ai"])
def explain_layout(request: LayoutExplanationRequest):
    """
    Generate an architectural explanation of a deterministic room layout.

    Interprets natural language preferences and layout geometry using
    Meta Muse Spark (or deterministic fallback when offline or in mock mode).
    Protected by concurrency limiter to prevent threadpool starvation.
    Strictly preserves deterministic coordinates.
    """
    acquired = _ai_semaphore.acquire(blocking=False)
    if not acquired:
        fallback = generate_mock_explanation(request)
        fallback.status = "fallback"
        fallback.model_used = "fallback-server-busy"
        fallback.reasoning_content = (
            "The AI explanation service is currently handling peak requests. "
            "Showing instant deterministic layout critique."
        )
        return fallback

    try:
        return generate_layout_explanation(request)
    finally:
        _ai_semaphore.release()


@app.post("/ai/segment-furniture", response_model=SegmentationResponse, tags=["ai"])
def segment_furniture(req: ImageSegmentationRequest):
    """
    Segment furniture items from room image using Meta SAM 3.1.

    Returns detected bounding boxes and categories. All items require
    user confirmation/metric calibration before adding to room inventory.
    """
    acquired = _sam_semaphore.acquire(blocking=False)
    if not acquired:
        fallback = generate_mock_segmentation(req.filename or "busy_upload.jpg")
        fallback.status = "fallback"
        fallback.model_used = "fallback-server-busy"
        fallback.message = "The SAM segmentation service is currently busy. Loaded simulated inventory."
        return fallback

    try:
        try:
            raw_bytes, detected_mime = _extract_image_bytes(req.image_base64)
            mime = req.mime_type or detected_mime
        except Exception:
            return SegmentationResponse(
                status="error",
                image_filename=req.filename or "upload.jpg",
                objects_detected=[],
                total_detected=0,
                model_used="validation",
                message="Invalid base64 image data payload.",
                requires_user_calibration=True,
            )

        return segment_furniture_image(
            image_bytes=raw_bytes,
            filename=req.filename or "upload.jpg",
            mime_type=mime,
        )
    finally:
        _sam_semaphore.release()


@app.post("/ai/generate-preview", response_model=ImagePreviewResponse, tags=["ai"])
def generate_preview(req: ImagePreviewRequest):
    """
    Generate an interior redesign preview using Meta Muse Image.

    Translates deterministic placement and aesthetic style into visual concept.
    Pixels represent artistic concepts and do NOT substitute for geometric validity.
    """
    acquired = _muse_image_semaphore.acquire(blocking=False)
    if not acquired:
        fallback = generate_mock_preview(req)
        fallback.status = "fallback"
        fallback.model_used = "fallback-server-busy"
        return fallback

    try:
        return generate_interior_preview(req)
    finally:
        _muse_image_semaphore.release()


@app.post("/ai/estimate-depth", response_model=DepthEstimationResponse, tags=["ai"])
def estimate_depth(req: DepthEstimationRequest):
    """
    Generate monocular depth map and object depth layers using Depth Anything V2.

    Computes relative/metric depth along camera Z-axis. Does NOT override
    user-confirmed room measurements or deterministic collision checks.
    """
    acquired = _depth_semaphore.acquire(blocking=False)
    if not acquired:
        fallback = generate_mock_depth_map(req)
        fallback.status = "fallback"
        fallback.model_used = "fallback-server-busy"
        fallback.disclaimer = "Depth service is currently busy. Showing instant synthetic depth gradient."
        return fallback

    try:
        return estimate_room_depth(req)
    finally:
        _depth_semaphore.release()




