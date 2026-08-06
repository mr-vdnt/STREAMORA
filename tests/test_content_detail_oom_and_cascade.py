import os
import sys
import time
import psutil
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.media.media_service import MediaPlatformService
from services.recommendation.recommendation_pipeline import RecommendationPipeline

def test_content_detail_fast_lookup_and_oom_prevention():
    """Verify Content Detail lookup completes in < 80ms with low memory footprint (< 15MB)."""
    print("\n--- Verifying Content Detail Fast Lookup & OOM Prevention ---")
    proc = psutil.Process()
    mem_before = proc.memory_info().rss / (1024 * 1024)

    start_time = time.time()
    media_svc = MediaPlatformService()
    bundle = media_svc.get_full_media_bundle(1)
    latency_ms = (time.time() - start_time) * 1000

    mem_after = proc.memory_info().rss / (1024 * 1024)
    mem_used = mem_after - mem_before

    assert bundle["content_id"] == 1
    assert latency_ms < 80.0, f"Detail lookup took {latency_ms:.2f}ms (Target: <80ms)"
    assert mem_used < 15.0, f"Memory overhead was {mem_used:.2f}MB (Target: <15MB)"
    print(f"[PASSED] Fast Detail Lookup Latency: {latency_ms:.2f}ms (<80ms SLA)")
    print(f"[PASSED] Memory Overhead: {mem_used:.2f}MB (<15MB SLA)")

def test_metadata_placeholder_sanitization():
    """Verify placeholders like 'Unknown Director', 'Undisclosed', 'Standalone', 'N/A' are stripped."""
    print("\n--- Verifying Metadata Placeholder Sanitization ---")
    raw_meta = {
        "title": "Inception",
        "director": "Unknown Director",
        "budget": "Undisclosed",
        "franchise": "Standalone",
        "studio": "Warner Bros",
        "rating": "N/A"
    }

    sanitized = MediaPlatformService.sanitize_metadata(raw_meta)
    assert "director" not in sanitized
    assert "budget" not in sanitized
    assert "franchise" not in sanitized
    assert "rating" not in sanitized
    assert sanitized["title"] == "Inception"
    assert sanitized["studio"] == "Warner Bros"
    print("[PASSED] Placeholder Metadata Sanitized Successfully")

def test_10_stage_fallback_cascade_never_empty():
    """Verify 10-Stage Fallback Cascade guarantees non-empty recommendation slates."""
    print("\n--- Verifying 10-Stage Fallback Recommendation Cascade ---")
    pipeline = RecommendationPipeline()
    import asyncio
    slate = asyncio.run(pipeline.generate_slate("demo_user", slate_type="personalized_home", limit=10))

    assert len(slate.items) >= 5, f"Slate item count was {len(slate.items)} (expected >= 5)"
    print(f"[PASSED] 10-Stage Cascade Returned {len(slate.items)} Recommended Items (Never Empty)")

def test_contextual_recommendation_shelves():
    """Verify contextual recommendation shelves ('Recommended Because...') for content detail modal."""
    print("\n--- Verifying Contextual Recommendation Shelves ---")
    pipeline = RecommendationPipeline()
    shelves = pipeline.generate_contextual_shelves(content_id=1, user_id="demo_user")

    assert len(shelves) >= 2, f"Shelves count was {len(shelves)} (expected >= 2)"
    for shelf in shelves:
        assert "title" in shelf
        assert "rationale" in shelf
        assert len(shelf["items"]) >= 1
    print(f"[PASSED] Generated {len(shelves)} Contextual Shelves with Rationales ('Recommended Because...')")

if __name__ == "__main__":
    test_content_detail_fast_lookup_and_oom_prevention()
    test_metadata_placeholder_sanitization()
    test_10_stage_fallback_cascade_never_empty()
    test_contextual_recommendation_shelves()
    print("\nALL CONTENT DETAIL OOM FIX & 10-STAGE FALLBACK TESTS PASSED (100%)!")
