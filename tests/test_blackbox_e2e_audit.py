"""
Black-Box E2E Production Path Audit Suite for Streamora V3.1.

Audits the end-to-end user path:
Auth Bootstrap -> Preference Onboarding Enforcement -> Home Feed (<50ms, Zero Synthetic Placeholders)
-> Content Details -> Contextual Recommendations -> Playback Progress -> Watchlist -> Observability.
"""
import time
import pytest
from fastapi.testclient import TestClient
from services.agent.main import app


@pytest.fixture
def client():
    return TestClient(app)


# --- 1. Auth, Onboarding & Bootstrap Audit ---

def test_blackbox_auth_bootstrap_and_onboarding(client):
    """Audit user registration, bootstrap, 409 onboarding enforcement, and onboarding completion."""
    username = f"audit_user_{time.time_ns()}"

    # Step 1: Register
    reg_resp = client.post("/api/v3/auth/register", json={
        "username": username,
        "email": f"{username}@streamora.ai",
        "password": "ProductionPassword123!"
    })
    assert reg_resp.status_code == 200
    reg_data = reg_resp.json()
    assert reg_data["onboarding_required"] is True

    # Step 2: Bootstrap query
    boot_resp = client.get("/api/v3/auth/bootstrap", params={"user_id": username})
    assert boot_resp.status_code == 200
    boot_data = boot_resp.json()
    assert boot_data["onboarding_required"] is True
    assert len(boot_data["categories"]) >= 5

    # Step 3: Un-onboarded user attempts GET /api/v3/home -> HTTP 409 Conflict
    home_409_resp = client.get("/api/v3/home", params={"user_id": username})
    assert home_409_resp.status_code == 409
    assert home_409_resp.json()["detail"] == "PREFERENCE_ONBOARDING_REQUIRED"

    # Step 4: Complete onboarding
    onboard_resp = client.post(
        "/api/v3/auth/onboarding",
        params={"user_id": username, "categories": ["Action & Adventure", "Sci-Fi & Fantasy"]}
    )
    assert onboard_resp.status_code == 200
    assert onboard_resp.json()["onboarding_required"] is False

    # Step 5: Onboarded user queries GET /api/v3/home -> HTTP 200 OK
    home_ok_resp = client.get("/api/v3/home", params={"user_id": username})
    assert home_ok_resp.status_code == 200
    assert home_ok_resp.json()["status"] == "SUCCESS"


# --- 2. Home Feed Latency & Zero-Placeholder Schema Audit ---

def test_blackbox_home_feed_latency_and_placeholder_audit(client):
    """Audit /api/v3/home latency (<50ms P95) and verify ZERO synthetic placeholders."""
    # Benchmark TTFB & total latency over 20 calls
    latencies_ms = []
    for _ in range(20):
        t0 = time.perf_counter()
        resp = client.get("/api/v3/home", params={"user_id": "demo_user"})
        elapsed_ms = (time.perf_counter() - t0) * 1000
        latencies_ms.append(elapsed_ms)
        assert resp.status_code == 200

    latencies_ms.sort()
    p95_index = int(len(latencies_ms) * 0.95)
    p95_ms = latencies_ms[p95_index]

    print(f"\n[Audit] GET /api/v3/home P95 Latency: {p95_ms:.2f}ms")
    assert p95_ms < 50.0, f"Home SLA exceeded 50ms P95: {p95_ms:.2f}ms"

    # Inspect payload structure
    home_data = client.get("/api/v3/home", params={"user_id": "demo_user"}).json()
    assert "sections" in home_data
    assert "hero" in home_data

    # Audit for synthetic placeholders across all home items
    FORBIDDEN_PATTERNS = ["85% match", "unknown director", "undisclosed", "rating × 10", "rating × 9.5"]
    raw_text = str(home_data).lower()
    for pattern in FORBIDDEN_PATTERNS:
        assert pattern not in raw_text, f"Forbidden synthetic placeholder detected in home feed: '{pattern}'"


# --- 3. Movie Details & Contextual Recommendations Audit ---

def test_blackbox_content_details_and_movie_recommendations(client):
    """Audit content details metadata & contextual recommendation candidate generation."""
    # Step 1: Content details for ID=1
    detail_resp = client.get("/api/v3/content/1")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()

    assert "id" in detail
    assert "title" in detail
    assert "rating" in detail

    # Step 2: Contextual recommendations for ID=1
    rec_resp = client.get("/api/v3/content/1/recommendations", params={"user_id": "demo_user"})
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()

    assert rec_data["content_id"] == 1
    assert "recommendations" in rec_data
    shelves = rec_data["recommendations"]
    assert len(shelves) >= 1, "Contextual recommendations must return at least 1 recommendation shelf"

    first_shelf = shelves[0]
    assert "items" in first_shelf or "title" in first_shelf


# --- 4. Playback, Watchlist & Observability Audit ---

def test_blackbox_playback_watchlist_and_observability(client):
    """Audit playback sync, watchlist, and health observability probes."""
    username = f"pb_user_{time.time_ns()}"

    # Step 1: Update playback progress
    pb_resp = client.put("/api/v3/playback/state", params={"user_id": username}, json={
        "content_id": 1,
        "position_seconds": 1200.0,
        "duration_seconds": 7200.0,
        "completed": False
    })
    assert pb_resp.status_code == 200

    # Step 2: Query continue watching
    cont_resp = client.get("/api/v3/playback/continue", params={"user_id": username})
    assert cont_resp.status_code == 200
    cont_data = cont_resp.json()
    assert len(cont_data["items"]) >= 1

    # Step 3: Add to Watchlist
    wl_add_resp = client.put("/api/v3/watchlist/1", params={"user_id": username})
    assert wl_add_resp.status_code == 200

    wl_get_resp = client.get("/api/v3/watchlist", params={"user_id": username})
    assert wl_get_resp.status_code == 200
    assert len(wl_get_resp.json()["items"]) >= 1

    # Step 4: Health Probes
    live_resp = client.get("/api/v3/health/live")
    assert live_resp.status_code == 200
    assert live_resp.json()["status"] == "ALIVE"

    ready_resp = client.get("/api/v3/ready")
    assert ready_resp.status_code == 200
    assert ready_resp.json()["status"] == "READY"

    deep_resp = client.get("/api/v3/health/deep")
    assert deep_resp.status_code == 200
    assert deep_resp.json()["status"] == "HEALTHY"
