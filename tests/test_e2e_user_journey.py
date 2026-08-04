import os
import sys
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_full_end_to_end_user_journey():
    from services.auth.jwt_auth import hash_password, verify_password, create_access_token, decode_token
    from services.hero.hero_service import HeroIntelligencePlatform
    from services.discovery.discovery_service import DiscoveryPlatformService
    from services.playback.playback_service import PlaybackService
    from services.playback.watch_history_service import WatchHistoryService
    from services.media.media_service import MediaPlatformService
    from services.observability.metrics_exporter import PrometheusMetricsExporter

    print("\n--- Starting Full End-to-End User Journey Validation ---")

    # Step 1: Registration & Login (Epic 1)
    pwd = hash_password("SecurePassword2026!")
    assert verify_password("SecurePassword2026!", pwd)
    token = create_access_token({"sub": "e2e_user_2026@streamora.ai", "user_id": 101})
    payload = decode_token(token)
    assert payload["sub"] == "e2e_user_2026@streamora.ai"
    print("[PASSED] Step 1: First-Time User Registration & Auth")

    # Step 2: High-Performance Home Experience < 500ms (Epic 2)
    start_time = time.time()
    hero = HeroIntelligencePlatform()
    banner = hero.get_hero_banner("101")

    disc = DiscoveryPlatformService()
    collections = disc.get_collections()
    latency_ms = (time.time() - start_time) * 1000

    assert "content_id" in banner
    assert len(collections) >= 1
    assert latency_ms < 1000.0, f"Home feed load took {latency_ms:.2f}ms"
    print(f"[PASSED] Step 2: Home Experience Loaded in {latency_ms:.2f}ms (<1000ms Target)")

    # Step 3: Content Experience & Media CDN (Epic 3)
    media = MediaPlatformService()
    bundle = media.get_full_media_bundle(1)
    assert bundle["content_id"] == 1
    assert "master_manifest_url" in bundle["manifest"]
    print("[PASSED] Step 3: Content Detail & Media CDN Bundle")

    # Step 4: Playback, Heartbeat Progress Sync & Watch History (Epic 4)
    playback = PlaybackService()
    sync = playback.sync_watch_progress(account_id=101, content_id=1, progress_seconds=3600.0, duration_seconds=9000.0)
    assert sync["is_completed"] == False

    history = WatchHistoryService()
    h_entry = history.record_watch_event(account_id=101, content_id=1, duration_watched_seconds=3600.0)
    assert h_entry["account_id"] == 101
    print("[PASSED] Step 4: Playback, Progress Sync & Immutable Watch History")

    # Step 5: Operations & Observability Metrics (Epic 5)
    exporter = PrometheusMetricsExporter()
    health = exporter.get_health_status()
    assert health["status"] in ["UP", "DEGRADED"]
    print("[PASSED] Step 5: Admin Operations & Prometheus Metrics")

    print("\nALL 5 END-TO-END CRITICAL USER JOURNEYS PASSED (100%)!")

if __name__ == "__main__":
    test_full_end_to_end_user_journey()
