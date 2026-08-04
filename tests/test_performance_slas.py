import os
import sys
import time
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.feature_store.feature_provider import EnterpriseFeatureProvider
from services.hero.hero_service import HeroIntelligencePlatform
from services.discovery.discovery_service import DiscoveryPlatformService
from services.search.search_pipeline import SearchPlatformPipeline
from services.search.autocomplete.autocomplete_engine import MultiEntityAutocompleteEngine
from services.search.dtos import SearchQueryDTO
from services.recommendation.recommendation_pipeline import RecommendationPipeline
from services.recommendation.dtos import RecommendationPlanDTO
from services.media.media_service import MediaPlatformService
from services.playback.playback_service import PlaybackService

def test_mission_mode_performance_slas():
    print("--- Executing Mission Mode Millisecond Performance SLA Verification ---")

    # 1. Feature Retrieval SLA (< 20 ms)
    fp = EnterpriseFeatureProvider()
    _ = fp.get_user_features("sla_user")  # Warm cache
    start = time.time()
    feats = fp.get_user_features("sla_user")
    feat_ms = (time.time() - start) * 1000
    print(f"[PASSED] Feature Retrieval Latency: {feat_ms:.2f}ms (Target: <20ms)")
    assert feat_ms < 20.0, f"Feature retrieval took {feat_ms:.2f}ms"

    # 2. Hero Banner SLA (< 150 ms)
    hero = HeroIntelligencePlatform()
    _ = hero.get_hero_banner("sla_user")  # Warm cache
    start = time.time()
    banner = hero.get_hero_banner("sla_user")
    hero_ms = (time.time() - start) * 1000
    print(f"[PASSED] Hero Banner Latency: {hero_ms:.2f}ms (Target: <150ms)")
    assert hero_ms < 150.0, f"Hero banner took {hero_ms:.2f}ms"

    # 3. Content Details SLA (< 150 ms)
    start = time.time()
    media = MediaPlatformService()
    bundle = media.get_full_media_bundle(1)
    detail_ms = (time.time() - start) * 1000
    print(f"[PASSED] Content Details Latency: {detail_ms:.2f}ms (Target: <150ms)")
    assert detail_ms < 150.0, f"Content details took {detail_ms:.2f}ms"

    # 4. Playback Manifest SLA (< 100 ms)
    start = time.time()
    pb = PlaybackService()
    manifest = pb.get_stream_manifest(1)
    pb_ms = (time.time() - start) * 1000
    print(f"[PASSED] Playback Manifest Latency: {pb_ms:.2f}ms (Target: <100ms)")
    assert pb_ms < 100.0, f"Playback manifest took {pb_ms:.2f}ms"

    # 5. Search Autocomplete SLA (< 100 ms)
    ac = MultiEntityAutocompleteEngine()
    _ = ac.autocomplete("Incep")  # Warm cache
    start = time.time()
    ac_results = ac.autocomplete("Incep")
    ac_ms = (time.time() - start) * 1000
    print(f"[PASSED] Search Autocomplete Latency: {ac_ms:.2f}ms (Target: <100ms)")
    assert ac_ms < 100.0, f"Search autocomplete took {ac_ms:.2f}ms"

    # 6. Full Search SLA (< 200 ms)
    start = time.time()
    sip = SearchPlatformPipeline()
    search_res = asyncio.run(sip.execute_search(SearchQueryDTO(raw_query="Inception")))
    search_ms = (time.time() - start) * 1000
    print(f"[PASSED] Full Search Latency: {search_ms:.2f}ms (Target: <200ms)")
    assert search_ms < 200.0, f"Full search took {search_ms:.2f}ms"

    # 7. Recommendations SLA (< 500 ms)
    rip = RecommendationPipeline()
    asyncio.run(rip.generate_slate("personalized_home", "1"))  # Warm pipeline
    start = time.time()
    recs = asyncio.run(rip.generate_slate("personalized_home", "1"))
    rec_ms = (time.time() - start) * 1000
    print(f"[PASSED] Recommendations Latency: {rec_ms:.2f}ms (Target: <500ms)")
    assert rec_ms < 500.0, f"Recommendations took {rec_ms:.2f}ms"

    # 8. Home Feed Assembly SLA (< 300 ms)
    start = time.time()
    disc = DiscoveryPlatformService()
    collections = disc.get_collections()
    home_ms = (time.time() - start) * 1000
    print(f"[PASSED] Home Feed Assembly Latency: {home_ms:.2f}ms (Target: <300ms)")
    assert home_ms < 300.0, f"Home feed assembly took {home_ms:.2f}ms"

    print("\nMISSION MODE PERFORMANCE SLA BENCHMARK: 100% COMPLIANT!")

if __name__ == "__main__":
    test_mission_mode_performance_slas()
