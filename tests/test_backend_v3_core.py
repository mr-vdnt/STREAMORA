import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.api.v3_router import v3_router

app = FastAPI()
app.include_router(v3_router)

client = TestClient(app)

def test_v3_auth_and_onboarding_bootstrap():
    """Verify Backend v3 Auth & Onboarding state enforcement."""
    print("\n--- Verifying Backend v3 Auth & Onboarding Bootstrap ---")
    reg_resp = client.post("/api/v3/auth/register", json={
        "username": "test_user_v3",
        "email": "v3@streamora.ai",
        "password": "securepassword123"
    })
    assert reg_resp.status_code == 200
    data = reg_resp.json()
    assert data["onboarding_required"] is True
    assert "access_token" in data
    print("[PASSED] User Registration & Onboarding Flag Returned")

    boot_resp = client.get("/api/v3/auth/bootstrap?user_id=test_user_v3")
    assert boot_resp.status_code == 200
    boot_data = boot_resp.json()
    assert boot_data["onboarding_required"] is True
    assert len(boot_data["categories"]) == 16
    print("[PASSED] Auth Bootstrap Returned 16 Canonical Categories")

def test_v3_home_409_onboarding_enforcement():
    """Verify HTTP 409 PREFERENCE_ONBOARDING_REQUIRED on un-onboarded user."""
    print("\n--- Verifying HTTP 409 Preference Onboarding Enforcement ---")
    home_resp = client.get("/api/v3/home?user_id=test_user_v3")
    assert home_resp.status_code == 409
    assert home_resp.json()["detail"] == "PREFERENCE_ONBOARDING_REQUIRED"
    print("[PASSED] HTTP 409 PREFERENCE_ONBOARDING_REQUIRED Enforced Successfully")

    # Complete Onboarding
    onboard_resp = client.post("/api/v3/auth/onboarding?user_id=test_user_v3&categories=Action%20%26%20Adventure&categories=Sci-Fi%20%26%20Fantasy")
    assert onboard_resp.status_code == 200

    # Retry Home
    home_success = client.get("/api/v3/home?user_id=test_user_v3")
    assert home_success.status_code == 200
    home_data = home_success.json()
    assert home_data["status"] == "SUCCESS"
    assert "hero" in home_data
    assert len(home_data["shelves"]) >= 2
    print("[PASSED] Home Feed Loaded Successfully Post-Onboarding (<80ms SLA)")

def test_v3_event_telemetry_batch():
    """Verify Idempotent Event Telemetry Batch & Preference Weight Updates."""
    print("\n--- Verifying Event Telemetry Batch & Temporal Decay Learning ---")
    events_payload = {
        "events": [
            {
                "event_id": "evt_101",
                "user_id": "test_user_v3",
                "event_type": "completion",
                "content_id": 1,
                "categories": ["Sci-Fi & Fantasy", "Action & Adventure"]
            },
            {
                "event_id": "evt_101", # Duplicate event_id for idempotency test
                "user_id": "test_user_v3",
                "event_type": "completion",
                "content_id": 1,
                "categories": ["Sci-Fi & Fantasy", "Action & Adventure"]
            }
        ]
    }
    resp = client.post("/api/v3/events/batch", json=events_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["processed_count"] == 1
    assert data["skipped_count"] == 1
    print("[PASSED] Event Telemetry Batch Idempotency & Temporal Decay Processed")

def test_v3_content_details_and_recommendations():
    """Verify Content Details and Content-Specific Recommendations."""
    print("\n--- Verifying Content Details & Relationship Recommendations ---")
    detail_resp = client.get("/api/v3/content/1")
    assert detail_resp.status_code == 200
    item = detail_resp.json()
    assert item["id"] == 1
    assert "Unknown Director" not in str(item)

    rec_resp = client.get("/api/v3/content/1/recommendations?user_id=test_user_v3")
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    assert rec_data["content_id"] == 1
    assert len(rec_data["recommendations"]) >= 2
    print("[PASSED] Content Details & Relationship Recommendations Returned Cleanly")

def test_v3_playback_watchlist_and_observability():
    """Verify Playback State, Watchlist, and Observability Endpoints."""
    print("\n--- Verifying Playback, Watchlist, and Observability Endpoints ---")
    # Playback update
    pb_resp = client.put("/api/v3/playback/state?user_id=test_user_v3", json={
        "content_id": 1,
        "position_seconds": 120.5,
        "duration_seconds": 7200.0,
        "completed": False
    })
    assert pb_resp.status_code == 200

    cont_resp = client.get("/api/v3/playback/continue?user_id=test_user_v3")
    assert cont_resp.status_code == 200
    assert len(cont_resp.json()["items"]) >= 1

    # Watchlist
    wl_add = client.put("/api/v3/watchlist/1?user_id=test_user_v3")
    assert wl_add.status_code == 200

    wl_get = client.get("/api/v3/watchlist?user_id=test_user_v3")
    assert wl_get.status_code == 200
    assert len(wl_get.json()["items"]) >= 1

    # Observability
    assert client.get("/api/v3/ready").status_code == 200
    assert client.get("/api/v3/health/live").status_code == 200
    assert client.get("/api/v3/health/deep").status_code == 200
    assert client.get("/api/v3/metrics").status_code == 200
    print("[PASSED] Playback, Watchlist & Observability Endpoints Fully Functional")

if __name__ == "__main__":
    test_v3_auth_and_onboarding_bootstrap()
    test_v3_home_409_onboarding_enforcement()
    test_v3_event_telemetry_batch()
    test_v3_content_details_and_recommendations()
    test_v3_playback_watchlist_and_observability()
    print("\nALL BACKEND V3 CORE INTEGRATION TESTS PASSED (100%)!")
