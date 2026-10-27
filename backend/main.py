"""
backend/main.py
---------------
RoomGenius AI — FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="RoomGenius AI",
    description="AI-powered room layout assistant — backend API",
    version="0.1.0",
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
