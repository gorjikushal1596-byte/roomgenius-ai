"""
backend/sam_service.py
----------------------
Meta SAM 3.1 (Segment Anything Model) integration service.

Detects furniture objects, spatial bounding boxes, and categories from uploaded
room photos to accelerate inventory population.

GOLDEN RULE:
    Pixels in photos do not establish metric physical dimensions without
    calibration. All detected objects return `calibrated=False` and require
    user confirmation/dimension input in the UI.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import urllib.error
import urllib.request
from typing import Optional

from schemas import (
    DetectedObject,
    NormalizedBoundingBox,
    SegmentationResponse,
)

logger = logging.getLogger(__name__)

# Security & Validation Constants
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SAM_TIMEOUT_SECONDS = 15

# Standard category mapping for room furniture
FURNITURE_CATEGORY_MAP = {
    "bed": "sleeping",
    "queen bed": "sleeping",
    "king bed": "sleeping",
    "mattress": "sleeping",
    "sofa": "seating",
    "couch": "seating",
    "chair": "seating",
    "armchair": "seating",
    "bench": "seating",
    "stool": "seating",
    "desk": "work",
    "table": "work",
    "dining table": "work",
    "coffee table": "work",
    "nightstand": "storage",
    "wardrobe": "storage",
    "closet": "storage",
    "dresser": "storage",
    "bookshelf": "storage",
    "bookcase": "storage",
    "cabinet": "storage",
}


def _sanitize_filename(name: str) -> str:
    """Strip directory traversal characters and restrict to safe alphanumeric characters."""
    base = os.path.basename(name)
    cleaned = re.sub(r"[^A-Za-z0-9_\-\.]", "_", base)
    return cleaned[:100] if cleaned else "room_upload.jpg"


def _get_sam_config() -> dict:
    """Retrieve SAM 3.1 configuration from environment variables."""
    api_key = os.getenv("META_API_KEY", "").strip()
    base_url = os.getenv("META_BASE_URL", "https://api.meta.ai/v1").rstrip("/")
    mock_mode = os.getenv("MOCK_AI", "false").strip().lower() in ("true", "1", "yes")

    return {
        "api_key": api_key,
        "base_url": base_url,
        "model": "sam-3.1",
        "mock_mode": mock_mode or not api_key,
    }


def is_sam_configured() -> bool:
    """Return True if real API credentials are configured and mock mode is off."""
    cfg = _get_sam_config()
    return bool(cfg["api_key"]) and not cfg["mock_mode"]


def generate_mock_segmentation(filename: str = "sample_room.jpg") -> SegmentationResponse:
    """
    Produce a deterministic, realistic room furniture segmentation response.

    Used when running offline, in test suites (0 credits consumed), or when
    the remote model API is unreachable.
    """
    sanitized = _sanitize_filename(filename)
    mock_items = [
        DetectedObject(
            id="detected-1",
            label="Bed",
            category="sleeping",
            confidence=0.96,
            box=NormalizedBoundingBox(ymin=0.20, xmin=0.15, ymax=0.75, xmax=0.55),
            suggested_width_cm=160.0,
            suggested_length_cm=200.0,
            calibrated=False,
        ),
        DetectedObject(
            id="detected-2",
            label="Nightstand",
            category="storage",
            confidence=0.91,
            box=NormalizedBoundingBox(ymin=0.35, xmin=0.60, ymax=0.65, xmax=0.75),
            suggested_width_cm=50.0,
            suggested_length_cm=45.0,
            calibrated=False,
        ),
        DetectedObject(
            id="detected-3",
            label="Desk",
            category="work",
            confidence=0.88,
            box=NormalizedBoundingBox(ymin=0.10, xmin=0.78, ymax=0.55, xmax=0.95),
            suggested_width_cm=120.0,
            suggested_length_cm=60.0,
            calibrated=False,
        ),
        DetectedObject(
            id="detected-4",
            label="Office Chair",
            category="seating",
            confidence=0.84,
            box=NormalizedBoundingBox(ymin=0.45, xmin=0.78, ymax=0.80, xmax=0.92),
            suggested_width_cm=65.0,
            suggested_length_cm=65.0,
            calibrated=False,
        ),
    ]

    return SegmentationResponse(
        status="success",
        image_filename=sanitized,
        objects_detected=mock_items,
        total_detected=len(mock_items),
        model_used="sam-3.1-mock",
        message="Simulated segmentation completed. Please confirm physical metric dimensions before adding to room layout.",
        requires_user_calibration=True,
    )


def segment_furniture_image(
    image_bytes: bytes,
    filename: str,
    mime_type: str = "image/jpeg",
    force_mock: bool = False,
) -> SegmentationResponse:
    """
    Segment furniture objects from uploaded room image bytes using Meta SAM 3.1.

    Validates size and format, calls Meta Model API Responses endpoint,
    and returns detected bounding boxes and categories.
    """
    sanitized_fn = _sanitize_filename(filename)

    # 1. Image Size & MIME Validation
    if not image_bytes:
        return SegmentationResponse(
            status="error",
            image_filename=sanitized_fn,
            objects_detected=[],
            total_detected=0,
            model_used="validation",
            message="Uploaded image file is empty.",
            requires_user_calibration=True,
        )

    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        return SegmentationResponse(
            status="error",
            image_filename=sanitized_fn,
            objects_detected=[],
            total_detected=0,
            model_used="validation",
            message=f"Image size exceeds maximum limit of {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)} MB.",
            requires_user_calibration=True,
        )

    clean_mime = mime_type.lower().split(";")[0].strip()
    if clean_mime not in ALLOWED_MIME_TYPES:
        return SegmentationResponse(
            status="error",
            image_filename=sanitized_fn,
            objects_detected=[],
            total_detected=0,
            model_used="validation",
            message=f"Unsupported image type '{clean_mime}'. Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}",
            requires_user_calibration=True,
        )

    # 2. Mock mode or missing credentials check
    config = _get_sam_config()
    if force_mock or config["mock_mode"]:
        logger.info("Using mock SAM segmentation for '%s'", sanitized_fn)
        return generate_mock_segmentation(sanitized_fn)

    # 3. Construct Meta SAM 3.1 Responses Payload
    b64_data = base64.b64encode(image_bytes).decode("utf-8")
    data_uri = f"data:{clean_mime};base64,{b64_data}"

    target_concepts = "bed, desk, sofa, chair, table, wardrobe, nightstand, cabinet, bookcase"
    payload = {
        "model": "sam-3.1",
        "stream": False,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"Detect and segment all interior room furniture: {target_concepts}",
                    },
                    {
                        "type": "input_image",
                        "image_url": data_uri,
                    },
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
        req = urllib.request.Request(endpoint, data=req_data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=SAM_TIMEOUT_SECONDS) as response:
            resp_bytes = response.read()
            resp_json = json.loads(resp_bytes.decode("utf-8"))

        # Parse response items
        raw_items = []
        if isinstance(resp_json, dict):
            # Check standard choices/output structures
            raw_output = resp_json.get("output") or resp_json.get("choices", [{}])[0].get("message", {}).get("content", "")
            if isinstance(raw_output, str):
                try:
                    parsed_output = json.loads(raw_output)
                    if isinstance(parsed_output, list):
                        raw_items = parsed_output
                    elif isinstance(parsed_output, dict):
                        raw_items = parsed_output.get("objects", [])
                except json.JSONDecodeError:
                    pass
            elif isinstance(raw_output, list):
                raw_items = raw_output

        detected: list[DetectedObject] = []
        for i, item in enumerate(raw_items[:30]):
            if not isinstance(item, dict):
                continue
            label = str(item.get("label", "furniture")).strip().lower()
            cat = FURNITURE_CATEGORY_MAP.get(label, "other")
            box_data = item.get("box", {})
            ymin = float(box_data.get("ymin", 0.0))
            xmin = float(box_data.get("xmin", 0.0))
            ymax = float(box_data.get("ymax", 1.0))
            xmax = float(box_data.get("xmax", 1.0))

            detected.append(
                DetectedObject(
                    id=f"sam-{i+1}",
                    label=label.title(),
                    category=cat,
                    confidence=float(item.get("confidence", 0.90)),
                    box=NormalizedBoundingBox(ymin=ymin, xmin=xmin, ymax=ymax, xmax=xmax),
                    suggested_width_cm=None,
                    suggested_length_cm=None,
                    calibrated=False,
                )
            )

        if not detected:
            logger.warning("SAM 3.1 returned zero parseable furniture detections; falling back to mock sample")
            fallback = generate_mock_segmentation(sanitized_fn)
            fallback.model_used = "sam-3.1-empty-fallback"
            return fallback

        return SegmentationResponse(
            status="success",
            image_filename=sanitized_fn,
            objects_detected=detected,
            total_detected=len(detected),
            model_used=config["model"],
            message=f"Detected {len(detected)} furniture items using Meta SAM 3.1. Please calibrate physical dimensions.",
            requires_user_calibration=True,
        )

    except urllib.error.HTTPError as e:
        logger.warning("SAM 3.1 HTTP error: %d %s", e.code, e.reason)
        fallback = generate_mock_segmentation(sanitized_fn)
        fallback.status = "fallback"
        fallback.model_used = f"fallback-due-to-http-{e.code}"
        fallback.message = f"Remote SAM 3.1 unavailable (HTTP {e.code}). Loaded simulated room inventory."
        return fallback

    except (urllib.error.URLError, TimeoutError) as e:
        logger.warning("SAM 3.1 network/timeout error: %s", e)
        fallback = generate_mock_segmentation(sanitized_fn)
        fallback.status = "fallback"
        fallback.model_used = "fallback-due-to-network-error"
        fallback.message = "Remote SAM 3.1 network timeout. Loaded simulated room inventory."
        return fallback

    except Exception as e:
        logger.exception("Unexpected error in SAM 3.1 segmentation: %s", e)
        fallback = generate_mock_segmentation(sanitized_fn)
        fallback.status = "fallback"
        fallback.model_used = "fallback-due-to-internal-error"
        return fallback

