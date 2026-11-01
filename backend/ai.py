"""
backend/ai.py
-------------
Meta Muse Spark AI Integration Service for RoomGenius AI.

Generates personalized architectural explanations grounded strictly in
deterministic 2D layout results. Employs Python stdlib (urllib.request)
to connect to the Meta Model API (or Baseten fallback), with built-in
mocking for credit conservation and testing.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
    # Load backend/.env if present
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

from pydantic import ValidationError

from schemas import LayoutExplanationRequest, LayoutExplanationResponse


def _get_env_config() -> dict[str, str]:
    """
    Retrieve Meta Model API configuration from environment.
    Guarantees Baseten credentials are never sent to the Meta endpoint.
    """
    meta_key = os.getenv("META_API_KEY", "").strip()
    baseten_key = os.getenv("BASETEN_API_KEY", "").strip()
    mock_mode = os.getenv("MOCK_AI", "false").lower() in ("true", "1", "yes")

    if meta_key:
        api_key = meta_key
        base_url = os.getenv("META_BASE_URL", "https://api.meta.ai/v1")
        model = os.getenv("META_MODEL", "muse-spark-1.3")
    elif baseten_key and os.getenv("BASETEN_BASE_URL"):
        api_key = baseten_key
        base_url = os.getenv("BASETEN_BASE_URL")
        model = os.getenv("BASETEN_MODEL", "meta-models/muse-spark-open")
    else:
        api_key = ""
        base_url = os.getenv("META_BASE_URL", "https://api.meta.ai/v1")
        model = os.getenv("META_MODEL", "muse-spark-1.3")

    return {
        "api_key": api_key,
        "base_url": base_url.rstrip("/"),
        "model": model,
        "mock_mode": mock_mode,
    }


def is_ai_configured() -> bool:
    """Check if a real Meta API key is available in environment."""
    config = _get_env_config()
    return bool(config["api_key"] and not config["mock_mode"])


def build_system_prompt() -> str:
    """
    Construct the system prompt enforcing deterministic safety rules.
    The AI is strictly prohibited from altering furniture coordinates or bounding boxes.
    """
    return (
        "You are RoomGenius AI, an architectural design consultant. "
        "CRITICAL RULE: The 2D coordinates (x, y) and orientations (0° or 90°) provided in the layout "
        "have been deterministically computed and validated by our physical geometry engine to guarantee "
        "zero collisions and room boundary compliance. "
        "You must NEVER alter, fabricate, or contradict these coordinates. "
        "Your task is to provide design reasoning, aesthetic context, traffic flow observations, "
        "and physical installation tips grounded strictly in this layout.\n\n"
        "Return your response ONLY as valid JSON matching this schema:\n"
        "{\n"
        '  "summary": "1-2 sentence overall summary of the room layout",\n'
        '  "design_reasoning": "Detailed architectural rationale for why this placement is practical, balanced, and aesthetically coherent",\n'
        '  "arrangement_tips": ["Tip 1: installation or lighting advice", "Tip 2: walkway clearance tip", ...],\n'
        '  "trade_offs": ["Note on room density, natural light, or unplaced items if any", ...]\n'
        "}"
    )


def build_user_prompt(req: LayoutExplanationRequest) -> str:
    """Build the prompt containing room facts and deterministic placements."""
    placed_str = "\n".join(
        f"- {item.name} (id: {item.id}): placed at (x={item.x} cm, y={item.y} cm), "
        f"effective footprint={item.width}x{item.length} cm, rotation={item.rotation}°"
        for item in req.placed_items
    ) or "None placed."

    unplaced_str = "\n".join(
        f"- {item.name} (id: {item.id}): rejected ({item.rejection_reason or 'No space'})"
        for item in req.unplaced_items
    ) or "None (all items successfully placed)."

    if req.preferences is not None:
        pref_dict = (
            req.preferences.model_dump(exclude_none=True)
            if hasattr(req.preferences, "model_dump")
            else req.preferences
        )
        preferences_str = json.dumps(pref_dict)
    else:
        preferences_str = "Default functional arrangement."

    return (
        f"Room Dimensions: Width = {req.room_width_cm} cm, Length = {req.room_length_cm} cm"
        + (f", Height = {req.room_height_cm} cm\n" if req.room_height_cm else "\n")
        + f"User Preferences: {preferences_str}\n\n"
        f"Placed Furniture ({len(req.placed_items)} items):\n{placed_str}\n\n"
        f"Unplaced Furniture ({len(req.unplaced_items)} items):\n{unplaced_str}\n\n"
        "Explain this arrangement to the user and return valid JSON."
    )


def generate_mock_explanation(req: LayoutExplanationRequest) -> LayoutExplanationResponse:
    """
    Generate a deterministic, realistic architectural explanation without consuming API credits.
    Used for local development, automated test suites, and graceful offline fallback.
    """
    placed_names = [item.name for item in req.placed_items]
    unplaced_names = [item.name for item in req.unplaced_items]
    room_area_m2 = (req.room_width_cm * req.room_length_cm) / 10000.0

    if not placed_names:
        summary = f"No furniture items were placed in this {req.room_width_cm:.0f}x{req.room_length_cm:.0f} cm room."
        reasoning = (
            "The room remains completely open. Either no items were requested or requested items "
            "exceeded the available boundary constraints."
        )
        tips = ["Add furniture items within the room perimeter to explore functional layout options."]
        trade_offs = ["Full unobstructed clearance, but currently non-functional as a living zone."]
    else:
        items_summary = ", ".join(placed_names[:3]) + ("..." if len(placed_names) > 3 else "")
        summary = (
            f"Optimized arrangement of {len(placed_names)} item(s) ({items_summary}) "
            f"across {room_area_m2:.1f} m² of living space."
        )
        reasoning = (
            f"The layout positions major pieces along perimeter boundary anchors to maximize central "
            f"circulation and preserve ingress paths. Rotations were applied deterministically where necessary "
            f"to respect room aspect ratio and eliminate boundary collisions."
        )
        tips = [
            f"Maintain at least 75-90 cm of clear walkway in front of {placed_names[0]} for comfortable transit.",
            "Position task or ambient lighting near corner boundaries to accentuate vertical visual depth.",
            "Verify wall outlet and radiator locations before finalizing exact physical placements.",
        ]
        trade_offs = []
        if unplaced_names:
            trade_offs.append(
                f"Could not place {len(unplaced_names)} item(s) ({', '.join(unplaced_names)}) due to room boundary "
                "or collision limits. Consider compact alternatives."
            )
        else:
            trade_offs.append("All inventory items fit comfortably with preserved functional clearance.")

    return LayoutExplanationResponse(
        status="success",
        summary=summary,
        design_reasoning=reasoning,
        arrangement_tips=tips,
        trade_offs=trade_offs,
        model_used="deterministic-mock-v1",
        reasoning_content="Deterministic spatial geometry heuristics verified zero overlaps and perimeter alignment.",
    )


def generate_layout_explanation(
    req: LayoutExplanationRequest,
    force_mock: bool = False,
    timeout_seconds: int = 45,
) -> LayoutExplanationResponse:
    """
    Request an AI explanation of the deterministic layout.
    Calls Meta Muse Spark API when configured and not in mock mode.
    Falls back gracefully to mock explanation on error.
    """
    config = _get_env_config()

    if force_mock or config["mock_mode"] or not config["api_key"]:
        return generate_mock_explanation(req)

    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(req)

    payload = {
        "model": config["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 1200,
        "reasoning_effort": "low",
        "stream": False,
    }

    url = f"{config['base_url']}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['api_key']}",
        "User-Agent": "RoomGenius-AI/0.3.0",
    }

    try:
        http_req = urllib.request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(http_req, timeout=timeout_seconds) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            choice = data["choices"][0]
            message = choice.get("message", {})
            raw_content = (message.get("content") or "").strip()
            reasoning_content = (message.get("reasoning_content") or "").strip()

            finish_reason = choice.get("finish_reason")
            if finish_reason == "length":
                logger.warning("Meta API response truncated (finish_reason=length)")
                fallback = generate_mock_explanation(req)
                fallback.status = "fallback"
                fallback.model_used = "fallback-due-to-token-truncation"
                fallback.reasoning_content = (
                    "Remote AI response was truncated by token limit. Showing deterministic explanation."
                )
                return fallback

            # Attempt to parse structured JSON from the model response
            parsed = _parse_model_json(raw_content)
            summary_val = parsed.get("summary") if parsed else None
            reasoning_val = parsed.get("design_reasoning") if parsed else None

            if (
                parsed
                and isinstance(summary_val, str)
                and summary_val.strip()
                and isinstance(reasoning_val, str)
                and reasoning_val.strip()
            ):
                try:
                    return LayoutExplanationResponse(
                        status="success",
                        summary=summary_val.strip(),
                        design_reasoning=reasoning_val.strip(),
                        arrangement_tips=parsed.get("arrangement_tips", []) if isinstance(parsed.get("arrangement_tips"), list) else [],
                        trade_offs=parsed.get("trade_offs", []) if isinstance(parsed.get("trade_offs"), list) else [],
                        model_used=config["model"],
                        reasoning_content=reasoning_content or None,
                    )
                except ValidationError as ve:
                    logger.warning("Meta API returned schema-invalid JSON: %s", ve)

            # Unparseable or malformed model output: use labeled deterministic fallback
            logger.warning("Meta API returned unparseable content (finish_reason=%s)", finish_reason)
            fallback = generate_mock_explanation(req)
            fallback.status = "fallback"
            fallback.model_used = "fallback-due-to-unparseable-response"
            fallback.reasoning_content = (
                "Remote AI response could not be parsed into structured format. Showing deterministic explanation."
            )
            return fallback

    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")[:300]
        except Exception:
            pass
        logger.warning("Meta API HTTP %s: %s", e.code, error_body)
        fallback = generate_mock_explanation(req)
        fallback.status = "fallback"
        fallback.model_used = f"fallback-due-to-http-{e.code}"
        fallback.reasoning_content = f"Remote AI provider returned HTTP {e.code}. Showing deterministic explanation."
        return fallback

    except Exception as exc:
        logger.warning("Meta API request failed: %s", exc)
        fallback = generate_mock_explanation(req)
        fallback.status = "fallback"
        fallback.model_used = "fallback-due-to-network-error"
        fallback.reasoning_content = "Remote AI provider was unreachable. Showing deterministic explanation."
        return fallback


def _parse_model_json(text: str) -> Optional[dict]:
    """Helper to extract JSON object from LLM response, stripping markdown fences if present."""
    if not text:
        return None
    cleaned = text.strip()
    # Strip markdown code blocks
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # Fallback: search for outermost JSON object brackets
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            data = json.loads(cleaned[first_brace : last_brace + 1])
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    return None
