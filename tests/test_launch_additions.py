import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from services.repository.catalog_db import CatalogRepository

def test_media_cdn_service():
    from services.media.media_service import MediaPlatformService
    service = MediaPlatformService()
    bundle = service.get_full_media_bundle(1, "/s3TBrRGB1iav7ySaNx3HjuEGBh6.jpg", "/oJu2W4fKGEXKGjF4tM9wPOvj2i.jpg")
    assert bundle["content_id"] == 1
    assert "master_manifest_url" in bundle["manifest"]
    assert "backdrop_hero" in bundle["artwork"]
    assert len(bundle["subtitles"]) >= 1

def test_watch_history_service():
    from services.playback.watch_history_service import WatchHistoryService
    history = WatchHistoryService()
    event = history.record_watch_event(account_id=42, content_id=1, duration_watched_seconds=1200.0, completed=True)
    assert event["account_id"] == 42
    assert event["completed"] == True
    user_hist = history.get_user_history(42)
    assert len(user_hist) >= 1

def test_notification_service():
    from services.notification.notification_service import NotificationService
    notif = NotificationService()
    n = notif.send_notification(account_id=42, title="New Release", message="Inception 2 is out now!", notification_type="new_release")
    assert n["account_id"] == 42
    unread = notif.get_user_notifications(42, unread_only=True)
    assert len(unread) >= 1

def test_admin_platform_service():
    from services.admin.admin_service import AdminPlatformService
    admin = AdminPlatformService()
    overview = admin.get_system_overview()
    assert overview["platform_status"] == "HEALTHY"
    assert "total_catalog_items" in overview["metrics"]

def test_observability_and_prometheus_exporter():
    from services.observability.metrics_exporter import PrometheusMetricsExporter
    exporter = PrometheusMetricsExporter()
    health = exporter.get_health_status()
    assert health["status"] in ["UP", "DEGRADED"]
    prom_text = exporter.export_prometheus_metrics()
    assert "streamora_uptime_seconds" in prom_text
    assert "streamora_database_status" in prom_text

if __name__ == "__main__":
    print("Executing Launch Additions Verification Suite...")
    test_media_cdn_service()
    print("[PASSED] Media & CDN Service (services/media/)")
    test_watch_history_service()
    print("[PASSED] Immutable Watch History Engine (services/playback/)")
    test_notification_service()
    print("[PASSED] Notification Platform (services/notification/)")
    test_admin_platform_service()
    print("[PASSED] Admin & CMS Platform (services/admin/)")
    test_observability_and_prometheus_exporter()
    print("[PASSED] Observability & Prometheus Metrics Exporter (services/observability/)")
    print("ALL 5 LAUNCH ADDITIONS PASSED VERIFICATION (100%)!")
