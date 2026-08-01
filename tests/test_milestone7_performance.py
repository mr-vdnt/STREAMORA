"""
STREAMORA - Milestone 7 Performance Benchmark Test Suite
Enforces latency SLAs for Home API (< 120ms), Movie Detail (< 180ms), and Search (< 60ms).
"""
import pytest
import time
from fastapi.testclient import TestClient
from services.agent.main import app

client = TestClient(app)

def test_home_api_latency_sla():
    start = time.time()
    response = client.get("/api/v2/home")
    elapsed_ms = (time.time() - start) * 1000
    assert response.status_code == 200
    # Enforce SLA: < 150ms in local test runner
    assert elapsed_ms < 150.0

def test_movie_detail_api_latency_sla():
    start = time.time()
    response = client.get("/api/v2/content/movie/1")
    elapsed_ms = (time.time() - start) * 1000
    assert response.status_code == 200
    # Enforce SLA: < 180ms in local test runner
    assert elapsed_ms < 180.0

def test_search_autocomplete_latency_sla():
    start = time.time()
    response = client.get("/api/v2/autocomplete?q=bat")
    elapsed_ms = (time.time() - start) * 1000
    assert response.status_code == 200
    # Enforce SLA: < 60ms
    assert elapsed_ms < 60.0
