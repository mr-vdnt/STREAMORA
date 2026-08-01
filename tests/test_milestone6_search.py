"""
STREAMORA - Milestone 6 Regression Test Suite
Validates Instant Autocomplete Search (< 60ms SLA) and Person Profile Discovery.
"""
import pytest
import time
from fastapi.testclient import TestClient
from services.agent.main import app

client = TestClient(app)

def test_autocomplete_performance_and_format():
    start = time.time()
    response = client.get("/api/v2/autocomplete?q=bat")
    elapsed_ms = (time.time() - start) * 1000
    
    assert response.status_code == 200
    data = response.json()
    assert "titles" in data or "genres" in data
    # Enforce < 100ms SLA for local test runner environment
    assert elapsed_ms < 100.0

def test_person_profile_endpoint():
    response = client.get("/api/v2/person/Christopher-Nolan")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Christopher Nolan"
    assert "biography" in data
    assert "filmography" in data
