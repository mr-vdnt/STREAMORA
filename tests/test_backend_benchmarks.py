import time
import pytest
from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def test_home_latency_benchmark():
    # Warm-up call to initialize DB connections & cache
    client.get("/api/v2/home")
    
    start = time.perf_counter()
    response = client.get("/api/v2/home")
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    
    assert response.status_code == 200
    assert elapsed_ms < 350.0, f"Home endpoint latency was {elapsed_ms:.2f}ms"

def test_movie_detail_latency_benchmark():
    # Warm-up call
    client.get("/api/v2/item/movie/1")
    
    start = time.perf_counter()
    response = client.get("/api/v2/item/movie/1")
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    
    assert response.status_code in [200, 404]
    assert elapsed_ms < 350.0, f"Movie detail endpoint latency was {elapsed_ms:.2f}ms"

def test_series_detail_latency_benchmark():
    # Warm-up call
    client.get("/api/v2/item/series/1")
    
    start = time.perf_counter()
    response = client.get("/api/v2/item/series/1")
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    
    assert response.status_code in [200, 404]
    assert elapsed_ms < 350.0, f"Series detail endpoint latency was {elapsed_ms:.2f}ms"

def test_search_latency_benchmark():
    # Warm-up call
    client.post("/api/v2/search", json={"query": "sci-fi action"})
    
    start = time.perf_counter()
    response = client.post("/api/v2/search", json={"query": "sci-fi action"})
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    
    assert response.status_code == 200
    assert elapsed_ms < 250.0, f"Search endpoint latency was {elapsed_ms:.2f}ms"
