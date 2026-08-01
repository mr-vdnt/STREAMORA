"""
STREAMORA - Milestone 8 Regression Test Suite
Validates Operational Demo Analytics Endpoint GET /api/v2/demo/system.
"""
import pytest
from fastapi.testclient import TestClient
from services.agent.main import app

client = TestClient(app)

def test_demo_system_endpoint_payload():
    response = client.get("/api/v2/demo/system")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL_HEALTHY"
    assert "catalog" in data
    assert "usage" in data
    assert "performance" in data
    assert "analytics" in data
    assert data["catalog"]["movies"] >= 0
    assert "cache_hit_ratio" in data["performance"]
    assert "uptime" in data["performance"]
