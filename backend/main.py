"""
backend/main.py
---------------
RoomGenius AI — FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from geometry import generate_layout
from ai import generate_layout_explanation, is_ai_configured
from schemas import (
    LayoutExplanationRequest,
    LayoutExplanationResponse,
    LayoutResponse,
    RoomInput,
)

app = FastAPI(
    title="RoomGenius AI",
    description="AI-powered room layout assistant — backend API",
    version="0.3.0",
)

# Allow Vite dev server (port 5173) to call the API during development.
# In production this should be replaced with the actual domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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


@app.post("/ai/explain", response_model=LayoutExplanationResponse, tags=["ai"])
def explain_layout(request: LayoutExplanationRequest):
    """
    Generate an architectural explanation of a deterministic room layout.

    Interprets natural language preferences and layout geometry using
    Meta Muse Spark (or deterministic fallback when offline or in mock mode).
    Strictly preserves deterministic coordinates.
    """
    return generate_layout_explanation(request)

