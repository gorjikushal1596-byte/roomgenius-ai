"""
backend/main.py
---------------
RoomGenius AI — FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from schemas import RoomInput

app = FastAPI(
    title="RoomGenius AI",
    description="AI-powered room layout assistant — backend API",
    version="0.2.0",
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


@app.post("/layout", tags=["room"])
def submit_layout(room: RoomInput):
    """
    Accept and validate a room layout submission.

    Pydantic validates all fields automatically — invalid payloads
    get a 422 with detailed error messages.

    Returns a summary of the accepted data (no placement logic yet).
    """
    return {
        "status": "accepted",
        "summary": {
            "room_width_cm": room.width,
            "room_length_cm": room.length,
            "room_height_cm": room.height,
            "unit": room.unit,
            "furniture_count": len(room.furniture),
            "has_preferences": room.preferences is not None,
        },
    }
