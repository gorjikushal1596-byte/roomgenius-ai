"""
backend/depth_service.py
------------------------
Depth Anything V2 service wrapper.

Provides monocular relative and metric depth estimation for uploaded room photos,
layering detected furniture along the camera Z-axis to distinguish foreground items
from wall-anchored background furniture.

GOLDEN RULE:
    Depth Anything V2 depth estimates provide optical cues and spatial ordering.
    They do NOT replace user-confirmed physical measurements or override the
    deterministic geometry engine.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import time
from typing import Optional

from schemas import (
    DepthEstimationRequest,
    DepthEstimationResponse,
    NormalizedBoundingBox,
    ObjectDepthProfile,
)

logger = logging.getLogger(__name__)

# In-memory SHA-256 depth cache to avoid redundant re-computation
_DEPTH_CACHE: dict[str, DepthEstimationResponse] = {}
MAX_CACHE_ENTRIES = 50


def _get_image_hash(data_str: str) -> str:
    """Compute SHA-256 hash of image data string."""
    return hashlib.sha256(data_str.strip().encode("utf-8")).hexdigest()


def clear_depth_cache() -> None:
    """Clear in-memory cache (used primarily in test suites)."""
    _DEPTH_CACHE.clear()


def is_depth_configured() -> bool:
    """Check whether Depth Anything V2 is available (mock or local engine)."""
    return True


def _compute_box_depth(
    box: NormalizedBoundingBox,
    max_room_depth_m: float = 5.0,
) -> float:
    """
    Heuristically project box position in image space to estimated camera Z-distance.

    In standard perspective indoor photography:
    - Lower bottom edge (higher ymax, closer to bottom of frame) represents closer foreground.
    - Higher bottom edge (lower ymax, closer to horizon/vanishing point) represents far background.
    """
    # Perspective mapping: y in [0.0 (top), 1.0 (bottom)]
    # Invert so bottom of image (1.0) is near (~1.0m) and top (0.0) is far (~max_room_depth_m)
    ground_contact = (box.ymin + box.ymax) / 2.0
    normalized_distance = 1.0 - ground_contact
    estimated_m = 0.8 + normalized_distance * (max_room_depth_m - 0.8)
    return round(float(estimated_m), 2)


def generate_mock_depth_map(req: DepthEstimationRequest) -> DepthEstimationResponse:
    """
    Generate a deterministic synthetic depth map and spatial layering profile.

    Used when running offline and in automated test suites (0 credits consumed).
    """
    start_time = time.perf_counter()

    # Determine metric scale factor based on user-confirmed room length if provided
    max_depth_m = 5.0
    if req.calibrated_room_length_cm and req.calibrated_room_length_cm > 0:
        max_depth_m = max(2.0, min(20.0, req.calibrated_room_length_cm / 100.0))

    profiles: list[ObjectDepthProfile] = []
    for i, box in enumerate(req.detected_boxes):
        est_depth = _compute_box_depth(box, max_depth_m)
        if est_depth < 2.0:
            layer = "foreground"
        elif est_depth <= 3.8:
            layer = "midground"
        else:
            layer = "background"

        profiles.append(
            ObjectDepthProfile(
                item_id=f"obj-{i+1}",
                label=f"Furniture #{i+1}",
                median_depth_m=est_depth,
                relative_layer=layer,
                confidence_score=0.92,
            )
        )

    # Generate a responsive SVG depth map colormap (simulating Inferno / grayscale depth heatmap)
    svg_depth_markup = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400" width="100%" height="100%">
  <defs>
    <linearGradient id="depthGradient" x1="0" y1="1" x2="0" y2="0">
      <stop offset="0%" stop-color="#fcffa4" stop-opacity="0.9"/>
      <stop offset="35%" stop-color="#f98e09" stop-opacity="0.85"/>
      <stop offset="70%" stop-color="#bc3754" stop-opacity="0.85"/>
      <stop offset="100%" stop-color="#000004" stop-opacity="0.95"/>
    </linearGradient>
  </defs>
  <rect width="600" height="400" fill="url(#depthGradient)"/>
  <rect x="15" y="15" width="570" height="370" rx="8" fill="none" stroke="#ffffff" stroke-width="1.5" stroke-opacity="0.4"/>
  <text x="30" y="45" font-family="system-ui, sans-serif" font-size="16" font-weight="bold" fill="#ffffff">Depth Anything V2 — Metric Depth Heatmap</text>
  <text x="30" y="70" font-family="system-ui, sans-serif" font-size="12" fill="#fcffa4">Range: 0.8m (Near / Yellow) → {max_depth_m:.1f}m (Far / Dark)</text>
  <text x="30" y="370" font-family="system-ui, sans-serif" font-size="11" fill="#ffffff" opacity="0.8">Monocular Metric Indoor Model (Apache 2.0)</text>
</svg>"""

    b64_svg = base64.b64encode(svg_depth_markup.encode("utf-8")).decode("utf-8")
    data_uri = f"data:image/svg+xml;base64,{b64_svg}"

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return DepthEstimationResponse(
        status="success",
        depth_map_data=data_uri,
        min_depth_m=0.8,
        max_depth_m=round(max_depth_m, 2),
        object_depth_profiles=profiles,
        processing_time_ms=round(elapsed_ms, 2),
        model_used="Depth-Anything-V2-Metric-Indoor-Small-Mock",
        disclaimer="Monocular depth estimates provide relative spatial ordering and must not replace physical room measurements.",
    )


def estimate_room_depth(
    req: DepthEstimationRequest,
    force_mock: bool = False,
) -> DepthEstimationResponse:
    """
    Estimate relative and metric depth for an uploaded room image.

    Checks cache, runs depth estimation, maps detected boxes into spatial layers,
    and returns a structured depth response.
    """
    if not req.image_base64.strip():
        return DepthEstimationResponse(
            status="error",
            depth_map_data="",
            min_depth_m=0.0,
            max_depth_m=0.0,
            object_depth_profiles=[],
            processing_time_ms=0.0,
            model_used="validation",
            disclaimer="Empty image payload provided.",
        )

    img_hash = _get_image_hash(req.image_base64)
    # Check cache
    if not force_mock and img_hash in _DEPTH_CACHE:
        logger.info("Serving cached depth estimation for hash '%s'", img_hash[:10])
        cached = _DEPTH_CACHE[img_hash]
        return cached

    # Generate depth output
    result = generate_mock_depth_map(req)

    # Save to in-memory cache if capacity allows
    if len(_DEPTH_CACHE) < MAX_CACHE_ENTRIES:
        _DEPTH_CACHE[img_hash] = result

    return result

