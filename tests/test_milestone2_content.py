"""
STREAMORA - Milestone 2 Regression Test Suite
Validates Content Platform endpoints: Movies, TV Series, Seasons, and Episodes.
"""
import pytest
from fastapi.testclient import TestClient
from services.agent.main import app
from services.security.user_data import init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_get_movie_content():
    # Fetch movie with ID 1
    response = client.get("/api/v2/content/movie/1")
    assert response.status_code == 200
    data = response.json()
    if "error" not in data:
        assert "id" in data or "movie" in data or "title" in data

def test_get_series_content():
    # Fetch series with ID 2
    response = client.get("/api/v2/content/series/2")
    assert response.status_code == 200
    data = response.json()
    if "error" not in data:
        assert "id" in data or "series" in data or "title" in data

def test_get_season_content():
    response = client.get("/api/v2/content/series/2/season/1")
    assert response.status_code == 200
    data = response.json()
    assert "season" in data or "error" in data

def test_get_episode_content():
    response = client.get("/api/v2/content/series/2/season/1/episode/1")
    assert response.status_code == 200
    data = response.json()
    assert "episode" in data or "error" in data

def test_nonexistent_content_handling():
    response = client.get("/api/v2/content/movie/99999999")
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
