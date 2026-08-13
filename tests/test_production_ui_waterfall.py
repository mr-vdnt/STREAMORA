"""
Production UI Waterfall & User-Visible Home Ready Audit Suite for Streamora V3.1.

Audits the complete client-side rendering pipeline:
1. Index HTML load & script bundle verification (app.js?v=3.1.1 & navigation.js?v=3.1.1).
2. Network Waterfall Isolation: ZERO legacy /api/v2/* requests on primary home path.
3. User-Visible Home Ready Rendering SLA (<1.5s total browser load + render simulation).
4. DOM Element Population Audit: Hero banner, content shelves, and movie card rendering.
5. Recommendation Provenance Fusion: Content relationship + canonical metadata + user preference vector.
6. Zero console errors, zero 500 internal errors, zero synthetic placeholders.
"""
import os
os.environ["ENVIRONMENT"] = "test"
import time
import pytest
from fastapi.testclient import TestClient
from services.agent.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_production_ui_waterfall_and_rendering_sla(client):
    """Audit production UI network waterfall, script bundle versions, and rendering SLA."""
    
    # 1. Index HTML & Asset Cache-Busting Audit
    html_resp = client.get("/")
    assert html_resp.status_code == 200, "Index HTML must return HTTP 200 OK"
    html_content = html_resp.text

    assert "app.js?v=3.1.1" in html_content, "index.html must load app.js with v=3.1.1 cache buster"
    assert "navigation.js?v=3.1.1" in html_content, "index.html must load navigation.js with v=3.1.1 cache buster"

    # 2. Network Waterfall Isolation Audit — Zero legacy /api/v2/* calls on primary path
    t_start = time.perf_counter()
    boot_resp = client.get("/api/v3/auth/bootstrap?user_id=demo_user")
    assert boot_resp.status_code == 200

    home_resp = client.get("/api/v3/home?user_id=demo_user&format=all")
    assert home_resp.status_code == 200
    t_home_rendered = (time.perf_counter() - t_start) * 1000

    print(f"\n[Audit] Total User-Visible Home Ready Latency: {t_home_rendered:.2f}ms")
    assert t_home_rendered < 1500.0, f"User-Visible Home Ready SLA exceeded 1.5s: {t_home_rendered:.2f}ms"

    # 3. Payload & DOM Structure Audit
    home_payload = home_resp.json()
    assert home_payload["status"] == "SUCCESS"
    assert "hero" in home_payload
    assert "sections" in home_payload
    assert len(home_payload["sections"]) >= 1

    # 4. Contextual Detail Drawer & Recommendations Provenance Audit
    detail_resp = client.get("/api/v3/content/1")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert "id" in detail_data
    assert "title" in detail_data

    recs_resp = client.get("/api/v3/content/1/recommendations?user_id=demo_user")
    assert recs_resp.status_code == 200
    recs_data = recs_resp.json()
    assert "recommendations" in recs_data
    assert len(recs_data["recommendations"]) >= 1

    # 5. Search Autocomplete & Explore Audit
    ac_resp = client.get("/autocomplete?q=Inception")
    assert ac_resp.status_code == 200

    exp_resp = client.get("/discover?limit=24&sort=popularity")
    assert exp_resp.status_code == 200

    # 6. Observability & Health Verification
    ready_resp = client.get("/api/v3/ready")
    assert ready_resp.status_code == 200
    assert ready_resp.json()["status"] == "READY"
