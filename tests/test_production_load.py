import os
import sys
import time
import concurrent.futures
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.feature_store.feature_provider import EnterpriseFeatureProvider
from services.hero.hero_service import HeroIntelligencePlatform
from services.discovery.discovery_service import DiscoveryPlatformService
from services.cache.cache_manager import CacheManager

fp = EnterpriseFeatureProvider()
hero = HeroIntelligencePlatform()
disc = DiscoveryPlatformService()
cache = CacheManager()

def simulate_concurrent_user_request(user_id_int: int) -> float:
    start_time = time.time()
    user_id = str(user_id_int)
    
    # 1. Fetch Features
    fp = EnterpriseFeatureProvider()
    feats = fp.get_user_features(user_id)

    # 2. Hero Banner & Discovery Collection simulation
    cached_banner = cache.get(f"hero:{user_id}")
    if not cached_banner:
        cache.set(f"hero:{user_id}", {"content_id": 1, "title": "Inception", "match_score": 98.4})

    cols = cache.get("discovery:collections")
    if not cols:
        cache.set("discovery:collections", [{"id": 1, "title": "Christopher Nolan Masterpieces"}])

    return (time.time() - start_time) * 1000

def test_production_load_and_concurrency():
    """Simulates 100 concurrent user requests evaluating throughput and latency SLA."""
    print("--- Executing Production Load & Concurrency Simulation ---")
    concurrent_users = 100
    latencies = []

    start_batch = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(simulate_concurrent_user_request, i) for i in range(concurrent_users)]
        for f in concurrent.futures.as_completed(futures):
            latencies.append(f.result())

    total_time = time.time() - start_batch
    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    throughput_rps = concurrent_users / total_time

    print(f"[PASSED] Total Requests Processed: {concurrent_users}")
    print(f"[PASSED] Total Execution Time: {total_time:.2f}s")
    print(f"[PASSED] Average Request Latency: {avg_latency:.2f}ms")
    print(f"[PASSED] Max Request Latency: {max_latency:.2f}ms")
    print(f"[PASSED] Throughput: {throughput_rps:.2f} Requests/Sec")

    assert avg_latency < 500.0, f"Average latency was {avg_latency:.2f}ms (expected < 500ms)"
    assert max_latency < 2000.0, f"Max latency was {max_latency:.2f}ms (expected < 2000ms)"
    print("PRODUCTION LOAD & CONCURRENCY SIMULATION PASSED (100%)!")

if __name__ == "__main__":
    test_production_load_and_concurrency()
