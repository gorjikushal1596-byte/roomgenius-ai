"""
backend/test_muse_image.py
--------------------------
Unit tests for Meta Muse Image service (Phase 1).
All tests run with 0 external API calls to conserve model credits.
"""

import json
from unittest.mock import MagicMock, patch
import pytest

from muse_image_service import (
    _build_architectural_prompt,
    generate_interior_preview,
    generate_mock_preview,
    is_muse_image_configured,
)
from schemas import (
    ImagePreviewRequest,
    PlacedFurnitureItem,
)


@pytest.fixture
def sample_preview_request():
    return ImagePreviewRequest(
        room_width_cm=400.0,
        room_length_cm=500.0,
        style="minimalist",
        placed_items=[
            PlacedFurnitureItem(
                id="bed-1",
                name="Queen Platform Bed",
                placed=True,
                x=50.0,
                y=50.0,
                width=160.0,
                length=200.0,
                rotation=0,
                within_bounds=True,
            ),
            PlacedFurnitureItem(
                id="desk-1",
                name="Solid Oak Desk",
                placed=True,
                x=250.0,
                y=350.0,
                width=120.0,
                length=60.0,
                rotation=90,
                within_bounds=True,
            ),
        ],
        custom_prompt_additions="warm oak finishes and large window light",
    )


def test_build_architectural_prompt(sample_preview_request):
    prompt = _build_architectural_prompt(sample_preview_request)
    assert "minimalist" in prompt
    assert "400cm" in prompt or "400" in prompt
    assert "Queen Platform Bed" in prompt
    assert "rotated 90°" in prompt
    assert "warm oak finishes" in prompt


def test_generate_mock_preview(sample_preview_request):
    res = generate_mock_preview(sample_preview_request)
    assert res.status == "success"
    assert res.format == "svg_data_uri"
    assert "data:image/svg+xml;base64," in res.image_data
    assert "Aesthetic concept preview only" in res.disclaimer
    assert "minimalist" in res.prompt_used.lower()


def test_generate_interior_preview_force_mock(sample_preview_request):
    res = generate_interior_preview(sample_preview_request, force_mock=True)
    assert res.status == "success"
    assert res.model_used == "muse-image-1.0-mock"
    assert res.image_data.startswith("data:image/svg+xml;base64,")


def test_generate_interior_preview_handles_b64_json_response(sample_preview_request):
    fake_b64_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    fake_response = json.dumps({
        "data": [
            {
                "b64_json": fake_b64_data,
            }
        ]
    }).encode("utf-8")

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value.read.return_value = fake_response

        with patch("muse_image_service._get_muse_image_config") as mock_cfg:
            mock_cfg.return_value = {
                "api_key": "dummy-key",
                "base_url": "https://api.meta.ai/v1",
                "model": "muse-image-1.0",
                "mock_mode": False,
            }
            res = generate_interior_preview(sample_preview_request)
            assert res.status == "success"
            assert res.format == "b64_json"
            assert res.image_data == f"data:image/png;base64,{fake_b64_data}"
            assert res.model_used == "muse-image-1.0"


def test_generate_interior_preview_handles_url_response(sample_preview_request):
    fake_url = "https://cdn.meta.ai/images/generated-interior-12345.png"
    fake_response = json.dumps({
        "data": [
            {
                "url": fake_url,
            }
        ]
    }).encode("utf-8")

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value.read.return_value = fake_response

        with patch("muse_image_service._get_muse_image_config") as mock_cfg:
            mock_cfg.return_value = {
                "api_key": "dummy-key",
                "base_url": "https://api.meta.ai/v1",
                "model": "muse-image-1.0",
                "mock_mode": False,
            }
            res = generate_interior_preview(sample_preview_request)
            assert res.status == "success"
            assert res.format == "url"
            assert res.image_data == fake_url


def test_generate_interior_preview_handles_http_error(sample_preview_request):
    with patch("urllib.request.urlopen") as mock_urlopen:
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.meta.ai/v1/images/generations",
            code=429,
            msg="Too Many Requests",
            hdrs={},
            fp=MagicMock(read=lambda: b'{"error": "rate limit"}'),
        )

        with patch("muse_image_service._get_muse_image_config") as mock_cfg:
            mock_cfg.return_value = {
                "api_key": "dummy-key",
                "base_url": "https://api.meta.ai/v1",
                "model": "muse-image-1.0",
                "mock_mode": False,
            }
            res = generate_interior_preview(sample_preview_request)
            assert res.status == "fallback"
            assert "fallback-due-to-http-429" in res.model_used
            assert len(res.image_data) > 0


def test_generate_interior_preview_handles_network_timeout(sample_preview_request):
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = TimeoutError("Network timeout")

        with patch("muse_image_service._get_muse_image_config") as mock_cfg:
            mock_cfg.return_value = {
                "api_key": "dummy-key",
                "base_url": "https://api.meta.ai/v1",
                "model": "muse-image-1.0",
                "mock_mode": False,
            }
            res = generate_interior_preview(sample_preview_request)
            assert res.status == "fallback"
            assert res.model_used == "fallback-due-to-network-error"

