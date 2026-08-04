import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi import FastAPI
from services.repository.catalog_db import CatalogRepository, UserAccount, DiscoveryCollection

repo = CatalogRepository()

def test_auth_service_directly():
    from services.auth.jwt_auth import hash_password, verify_password, create_access_token, decode_token
    h = hash_password("pass123")
    assert verify_password("pass123", h)
    token = create_access_token({"sub": "direct_user@streamora.ai"})
    payload = decode_token(token)
    assert payload["sub"] == "direct_user@streamora.ai"

def test_discovery_service_directly():
    from services.discovery.discovery_service import DiscoveryPlatformService
    service = DiscoveryPlatformService()
    cols = service.get_collections()
    assert len(cols) >= 1
    hub = service.get_hub("sci-fi")
    assert hub.slug == "sci-fi"

def test_hero_service_directly():
    from services.hero.hero_service import HeroIntelligencePlatform
    hero = HeroIntelligencePlatform()
    banner = hero.get_hero_banner()
    assert "content_id" in banner
    assert "trailer_url" in banner

def test_playback_service_directly():
    from services.playback.playback_service import PlaybackService
    playback = PlaybackService()
    m = playback.get_stream_manifest(1)
    assert m["stream_format"] == "HLS"
    p = playback.sync_watch_progress(account_id=99, content_id=1, progress_seconds=300.0, duration_seconds=6000.0)
    assert p["is_completed"] == False
    cw = playback.get_continue_watching(account_id=99)
    assert len(cw) >= 1

if __name__ == "__main__":
    print("Executing Direct Milestone A Launch Platform Tests...")
    test_auth_service_directly()
    print("[PASSED] Workstream 3 (Auth & JWT Security)")
    test_discovery_service_directly()
    print("[PASSED] Workstream 1 (Discovery Platform Hubs & Collections)")
    test_hero_service_directly()
    print("[PASSED] Workstream 2 (Hero Intelligence Platform Banners)")
    test_playback_service_directly()
    print("[PASSED] Workstream 4 (Playback & Progress Sync)")
    print("ALL MILESTONE A LAUNCH PLATFORM TESTS PASSED (100%)!")
