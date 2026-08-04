import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

def test_product_analytics_engine():
    from services.analytics.analytics_service import ProductAnalyticsEngine
    engine = ProductAnalyticsEngine()

    # Track custom event
    evt = engine.track_event("hero_click", "user_101", content_id=1, metadata={"position": 1})
    assert evt["event_name"] == "hero_click"
    assert evt["user_id"] == "user_101"

    # Fetch dashboard metrics
    metrics = engine.get_dashboard_metrics()
    assert "active_users" in metrics
    assert "engagement_metrics" in metrics
    assert metrics["engagement_metrics"]["hero_banner_ctr_percent"] > 0

if __name__ == "__main__":
    print("Executing Product Analytics Engine Verification Suite...")
    test_product_analytics_engine()
    print("[PASSED] Product Analytics Engine & Metric Dashboard (analytics_service.py)")
    print("PRODUCT ANALYTICS VERIFICATION COMPLETE (100%)!")
