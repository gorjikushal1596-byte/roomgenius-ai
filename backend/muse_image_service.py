"""
backend/muse_image_service.py
-----------------------------
Meta Muse Image integration service.

Generates photorealistic interior redesign previews grounded in the
deterministic layout geometry and user-selected aesthetic styles.

GOLDEN RULE:
    Visual redesign pixels are purely aesthetic concept previews. They do NOT
    substitute for or prove physical geometric validity. The deterministic 2D
    SVG floorplan remains the physical ground truth.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import urllib.error
import urllib.request
from typing import Optional

from schemas import (
    ImagePreviewRequest,
    ImagePreviewResponse,
)

logger = logging.getLogger(__name__)

MUSE_IMAGE_TIMEOUT_SECONDS = 20


def _get_muse_image_config() -> dict:
    """Retrieve Muse Image configuration from environment variables."""
    api_key = os.getenv("META_API_KEY", "").strip()
    base_url = os.getenv("META_BASE_URL", "https://api.meta.ai/v1").rstrip("/")
    mock_mode = os.getenv("MOCK_AI", "false").strip().lower() in ("true", "1", "yes")

    return {
        "api_key": api_key,
        "base_url": base_url,
        "model": "muse-image-1.0",
        "mock_mode": mock_mode or not api_key,
    }


def is_muse_image_configured() -> bool:
    """Return True if real API credentials are configured and mock mode is off."""
    cfg = _get_muse_image_config()
    return bool(cfg["api_key"]) and not cfg["mock_mode"]


def _build_architectural_prompt(req: ImagePreviewRequest) -> str:
    """Construct an architectural text prompt grounded in deterministic placement facts."""
    placed_summary = []
    for item in req.placed_items:
        coords = f"at ({item.x:.0f}, {item.y:.0f}) cm" if item.x is not None and item.y is not None else ""
        rot = " rotated 90°" if item.rotation == 90 else ""
        placed_summary.append(f"{item.name} {coords}{rot}".strip())

    items_str = ", ".join(placed_summary) if placed_summary else "open spacious room layout"

    base_prompt = (
        f"Award-winning architectural interior design photography of a {req.style} room, "
        f"dimensions {req.room_width_cm:.0f}cm wide by {req.room_length_cm:.0f}cm deep. "
        f"Room layout arrangement: {items_str}. "
        f"High quality materials, balanced ambient lighting, clean sightlines, photorealistic, 8k resolution."
    )

    if req.custom_prompt_additions:
        clean_custom = req.custom_prompt_additions.strip()[:200]
        base_prompt += f" Specific design accents: {clean_custom}."

    return base_prompt


def generate_mock_preview(req: ImagePreviewRequest) -> ImagePreviewResponse:
    """
    Generate an instant SVG-based visual preview without calling external APIs.

    Provides a clean, aesthetic rendering offline and during tests (0 credits used).
    """
    prompt = _build_architectural_prompt(req)

    # Generate a responsive aesthetic concept placeholder as an SVG Data URI
    style_color = {
        "minimalist": "#4f46e5",
        "modern": "#2563eb",
        "cozy": "#d97706",
        "traditional": "#059669",
        "industrial": "#475569",
    }.get(req.style.lower(), "#6366f1")

    item_chips = "".join(
        f'<rect x="{30 + (i % 3) * 240}" y="{320 + (i // 3) * 60}" width="220" height="45" rx="8" fill="#ffffff" stroke="{style_color}" stroke-width="1.5"/>'
        f'<text x="{45 + (i % 3) * 240}" y="{348 + (i // 3) * 60}" font-family="system-ui, sans-serif" font-size="13" font-weight="600" fill="#1e293b">{item.name[:24]}</text>'
        for i, item in enumerate(req.placed_items[:6])
    )

    svg_markup = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="100%" height="100%">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#f8fafc"/>
      <stop offset="100%" stop-color="#e2e8f0"/>
    </linearGradient>
  </defs>
  <rect width="800" height="500" fill="url(#bg)"/>
  <rect x="20" y="20" width="760" height="460" rx="16" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>
  <rect x="40" y="40" width="720" height="120" rx="12" fill="{style_color}" opacity="0.1"/>
  <text x="60" y="85" font-family="system-ui, sans-serif" font-size="24" font-weight="bold" fill="#0f172a">RoomGenius AI — {req.style.title()} Concept Preview</text>
  <text x="60" y="115" font-family="system-ui, sans-serif" font-size="14" fill="#475569">Room Dimensions: {req.room_width_cm:.0f} × {req.room_length_cm:.0f} cm · {len(req.placed_items)} Items Arranged</text>
  <rect x="40" y="180" width="720" height="80" rx="8" fill="#f1f5f9"/>
  <text x="60" y="215" font-family="system-ui, sans-serif" font-size="13" font-weight="600" fill="#334155">Simulated Meta Muse Image Render (Offline / Mock Mode)</text>
  <text x="60" y="238" font-family="system-ui, sans-serif" font-size="12" fill="#64748b">Prompt: {prompt[:85]}...</text>
  <text x="40" y="300" font-family="system-ui, sans-serif" font-size="14" font-weight="bold" fill="#1e293b">Planned Layout Elements:</text>
  {item_chips}
  <text x="400" y="460" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" fill="#94a3b8">⚠️ Aesthetic concept preview only. Refer to 2D Floorplan for precise physical dimensions.</text>
</svg>"""

    b64_svg = base64.b64encode(svg_markup.encode("utf-8")).decode("utf-8")
    data_uri = f"data:image/svg+xml;base64,{b64_svg}"

    return ImagePreviewResponse(
        status="success",
        image_data=data_uri,
        format="svg_data_uri",
        prompt_used=prompt,
        model_used="muse-image-1.0-mock",
        disclaimer="Aesthetic concept preview only. Refer to 2D Floorplan for precise physical dimensions and clearances.",
    )


def generate_interior_preview(
    req: ImagePreviewRequest,
    force_mock: bool = False,
) -> ImagePreviewResponse:
    """
    Generate an interior redesign preview using Meta Muse Image.

    Translates deterministic layout facts and aesthetic style into a prompt,
    calls the Meta Model API image generation endpoint, and returns the result.
    """
    prompt = _build_architectural_prompt(req)
    config = _get_muse_image_config()

    if force_mock or config["mock_mode"]:
        logger.info("Using mock Muse Image preview for style '%s'", req.style)
        return generate_mock_preview(req)

    # Construct Meta Model API Responses payload for muse-image-1.0
    payload = {
        "model": "muse-image-1.0",
        "stream": False,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt,
                    }
                ],
            }
        ],
    }

    req_data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['api_key']}",
        "User-Agent": "RoomGeniusAI/0.3.0",
    }

    endpoint = f"{config['base_url']}/responses"

    try:
        http_req = urllib.request.Request(endpoint, data=req_data, headers=headers, method="POST")
        with urllib.request.urlopen(http_req, timeout=MUSE_IMAGE_TIMEOUT_SECONDS) as response:
            resp_bytes = response.read()
            resp_json = json.loads(resp_bytes.decode("utf-8"))

        # Extract generated image data
        image_data = ""
        format_type = "b64_json"

        if isinstance(resp_json, dict):
            # 1. Native Meta Model API /responses structure (image_generation_call)
            for item in resp_json.get("output", []):
                if isinstance(item, dict) and item.get("type") in ("image_generation_call", "image"):
                    res_val = item.get("result", "")
                    if isinstance(res_val, str) and res_val.strip():
                        if res_val.startswith("data:image"):
                            image_data = res_val
                        elif res_val.startswith("http://") or res_val.startswith("https://"):
                            image_data = res_val
                            format_type = "url"
                        else:
                            # Base64 WebP image data
                            image_data = f"data:image/webp;base64,{res_val.strip()}"
                            format_type = "b64_json"
                        break

            # 2. Compatibility check for OpenAI-style responses (for mocks and unit tests)
            if not image_data:
                data_arr = resp_json.get("data", [])
                if data_arr and isinstance(data_arr[0], dict):
                    first = data_arr[0]
                    if "b64_json" in first:
                        image_data = f"data:image/png;base64,{first['b64_json']}"
                        format_type = "b64_json"
                    elif "url" in first:
                        image_data = first["url"]
                        format_type = "url"

        if not image_data:
            logger.warning("Muse Image returned no valid image payload; using mock preview fallback")
            fallback = generate_mock_preview(req)
            fallback.status = "fallback"
            fallback.model_used = "muse-image-empty-fallback"
            return fallback

        return ImagePreviewResponse(
            status="success",
            image_data=image_data,
            format=format_type,
            prompt_used=prompt,
            model_used=config["model"],
            disclaimer="Aesthetic concept preview only. Refer to 2D Floorplan for precise physical dimensions and clearances.",
        )

    except urllib.error.HTTPError as e:
        logger.warning("Muse Image HTTP error: %d %s", e.code, e.reason)
        fallback = generate_mock_preview(req)
        fallback.status = "fallback"
        fallback.model_used = f"fallback-due-to-http-{e.code}"
        return fallback

    except (urllib.error.URLError, TimeoutError) as e:
        logger.warning("Muse Image network/timeout error: %s", e)
        fallback = generate_mock_preview(req)
        fallback.status = "fallback"
        fallback.model_used = "fallback-due-to-network-error"
        return fallback

    except Exception as e:
        logger.exception("Unexpected error in Muse Image generation: %s", e)
        fallback = generate_mock_preview(req)
        fallback.status = "fallback"
        fallback.model_used = "fallback-due-to-internal-error"
        return fallback

