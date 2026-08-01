"""
STREAMORA - Milestone 4 Regression Test Suite
Validates Cinematic Movie and Series Detail orchestrator payloads.
"""
import pytest
from fastapi.testclient import TestClient
from services.agent.main import app

client = TestClient(app)

def test_movie_detail_orchestration():
    response = client.get("/api/v2/content/movie/1")
    assert response.status_code == 200
    data = response.json()
    assert "movie" in data
    assert "media_package" in data
    assert "credits" in data
    assert "ai" in data
    assert "recommendations" in data

def test_series_detail_orchestration():
    response = client.get("/api/v2/content/series/2")
    assert response.status_code == 200
    data = response.json()
    assert "series" in data or "id" in data or "title" in data
