"""
backend/test_ai.py
------------------
Comprehensive unit and integration tests for Meta Muse Spark AI layout explanation service.
All tests run with ZERO real API credit consumption (using mocked fixtures and local engine).
"""

import json
from unittest.mock import MagicMock, patch
import urllib.error
import pytest
from fastapi.testclient import TestClient

from main import app
from schemas import LayoutExplanationRequest, PlacedFurnitureItem
from ai import (
    build_system_prompt,
    build_user_prompt,
    generate_layout_explanation,
    generate_mock_explanation,
    is_ai_configured,
)

client = TestClient(app)


@pytest.fixture
def sample_explanation_request():
    return LayoutExplanationRequest(
        room_width_cm=400.0,
        room_length_cm=500.0,
        room_height_cm=260.0,
        preferences={"style": "minimalist", "lighting": "natural"},
        placed_items=[
            PlacedFurnitureItem(
                id="bed-1",
                name="Queen Bed",
                placed=True,
                x=0.0,
                y=0.0,
                width=160.0,
                length=200.0,
                rotation=0,
                within_bounds=True,
            ),
            PlacedFurnitureItem(
                id="desk-1",
                name="Writing Desk",
                placed=True,
                x=160.0,
                y=0.0,
                width=120.0,
                length=60.0,
                rotation=90,
                within_bounds=True,
            ),
        ],
        unplaced_items=[],
    )


@pytest.fixture
def sample_request_with_unplaced():
    return LayoutExplanationRequest(
        room_width_cm=200.0,
        room_length_cm=200.0,
        preferences={"vibe": "cozy"},
        placed_items=[
            PlacedFurnitureItem(
                id="chair-1",
                name="Armchair",
                placed=True,
                x=0.0,
                y=0.0,
                width=90.0,
                length=90.0,
                rotation=0,
                within_bounds=True,
            )
        ],
        unplaced_items=[
            PlacedFurnitureItem(
                id="sofa-1",
                name="3-Seater Sofa",
                placed=False,
                width=240.0,
                length=100.0,
                within_bounds=False,
                rejection_reason="Exceeds room boundary constraints",
            )
        ],
    )


def test_ai_status_endpoint():
    """Verify /ai/status returns boolean configured flag."""
    resp = client.get("/ai/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "configured" in data
    assert isinstance(data["configured"], bool)


def test_system_prompt_mandates_deterministic_preservation():
    """Verify system prompt enforces non-contradiction of deterministic geometry."""
    sys_prompt = build_system_prompt()
    assert "deterministic" in sys_prompt.lower()
    assert "never alter, fabricate, or contradict" in sys_prompt.lower()
    assert "geometry engine" in sys_prompt.lower()


def test_user_prompt_contains_exact_coordinates(sample_explanation_request):
    """Verify user prompt embeds exact coordinates, rotation, and dimensions."""
    user_prompt = build_user_prompt(sample_explanation_request)
    assert "Width = 400.0 cm" in user_prompt
    assert "Length = 500.0 cm" in user_prompt
    assert "Queen Bed" in user_prompt
    assert "x=0.0 cm, y=0.0 cm" in user_prompt
    assert "rotation=0°" in user_prompt
    assert "rotation=90°" in user_prompt


def test_mock_explanation_generation(sample_explanation_request):
    """Verify generate_mock_explanation produces valid, structured response without API calls."""
    res = generate_mock_explanation(sample_explanation_request)
    assert res.status == "success"
    assert "Queen Bed" in res.summary
    assert len(res.arrangement_tips) >= 2
    assert len(res.trade_offs) >= 1
    assert res.model_used == "deterministic-mock-v1"


def test_mock_explanation_with_unplaced_items(sample_request_with_unplaced):
    """Verify trade-offs mention rejected items."""
    res = generate_mock_explanation(sample_request_with_unplaced)
    assert res.status == "success"
    trade_offs_text = " ".join(res.trade_offs)
    assert "3-Seater Sofa" in trade_offs_text


def test_mock_explanation_empty_room():
    """Verify empty room produces coherent open space message."""
    empty_req = LayoutExplanationRequest(
        room_width_cm=300.0,
        room_length_cm=300.0,
        placed_items=[],
        unplaced_items=[],
    )
    res = generate_mock_explanation(empty_req)
    assert res.status == "success"
    assert "No furniture items were placed" in res.summary


def test_api_explain_endpoint_force_mock(sample_explanation_request):
    """Verify POST /ai/explain returns 200 and schema-compliant JSON in mock mode."""
    with patch("ai._get_env_config") as mock_cfg:
        mock_cfg.return_value = {
            "api_key": "",
            "base_url": "https://api.meta.ai/v1",
            "model": "muse-spark-1.3",
            "mock_mode": True,
        }
        resp = client.post("/ai/explain", json=sample_explanation_request.model_dump())
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "summary" in data
        assert "design_reasoning" in data
        assert isinstance(data["arrangement_tips"], list)
        assert isinstance(data["trade_offs"], list)


def test_api_explain_missing_required_dimensions():
    """Verify POST /ai/explain rejects invalid payload missing room dimensions."""
    resp = client.post("/ai/explain", json={"preferences": {}})
    assert resp.status_code == 422


def test_api_explain_rejects_excessive_items():
    """Verify POST /ai/explain rejects requests with more than 100 items (DoS protection)."""
    excessive_items = [
        {
            "id": f"item-{i}",
            "name": f"Item {i}",
            "placed": True,
            "x": 0.0,
            "y": 0.0,
            "width": 10.0,
            "length": 10.0,
            "rotation": 0,
            "within_bounds": True,
        }
        for i in range(101)
    ]
    payload = {
        "room_width_cm": 500.0,
        "room_length_cm": 500.0,
        "placed_items": excessive_items,
    }
    resp = client.post("/ai/explain", json=payload)
    assert resp.status_code == 422



def test_api_explain_graceful_fallback_on_http_error(sample_explanation_request):
    """Verify HTTP error from remote provider falls back cleanly without 500 crash."""
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_error = urllib.error.HTTPError(
            url="https://api.meta.ai/v1/chat/completions",
            code=429,
            msg="Rate limit exceeded",
            hdrs={},
            fp=MagicMock(read=lambda: b'{"error": "Quota reached"}'),
        )
        mock_urlopen.side_effect = mock_error

        # Ensure not in mock mode so urlopen is called
        with patch("ai._get_env_config") as mock_cfg:
            mock_cfg.return_value = {
                "api_key": "dummy-key",
                "base_url": "https://api.meta.ai/v1",
                "model": "muse-spark-1.3",
                "mock_mode": False,
            }
            res = generate_layout_explanation(sample_explanation_request)
            assert res.status == "fallback"
            assert "fallback-due-to-http-429" in res.model_used
            assert len(res.arrangement_tips) > 0


def test_api_explain_graceful_fallback_on_timeout(sample_explanation_request):
    """Verify network timeout triggers fallback gracefully."""
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = TimeoutError("Connection timed out")

        with patch("ai._get_env_config") as mock_cfg:
            mock_cfg.return_value = {
                "api_key": "dummy-key",
                "base_url": "https://api.meta.ai/v1",
                "model": "muse-spark-1.3",
                "mock_mode": False,
            }
            res = generate_layout_explanation(sample_explanation_request)
            assert res.status == "fallback"
            assert "fallback-due-to-network-error" in res.model_used

