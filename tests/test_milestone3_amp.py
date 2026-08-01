"""
STREAMORA - Milestone 3 Regression Test Suite
Validates AMP Lite Media Package endpoints, YouTube video embed payloads, and fallback URLs.
"""
import pytest
from fastapi.testclient import TestClient
from services.agent.main import app

client = TestClient(app)

def test_get_media_package_default():
    response = client.get("/api/v2/media-package/1")
    assert response.status_code == 200
    data = response.json()
    assert "poster" in data
    assert "backdrop" in data
    assert "primary_video" in data
    assert data["primary_video"]["player_type"] == "embed_iframe"
    assert "fallback" in data["primary_video"]
    assert "youtube.com" in data["primary_video"]["fallback"]["url"]

def test_get_typed_media_package_movie():
    response = client.get("/api/v2/media-package/movie/1")
    assert response.status_code == 200
    data = response.json()
    assert data["content_id"] == 1
    assert "providers" in data

def test_get_typed_media_package_series():
    response = client.get("/api/v2/media-package/series/2")
    assert response.status_code == 200
    data = response.json()
    assert data["content_id"] == 2
