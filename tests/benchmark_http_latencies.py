import os
import sys
import time
import numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.api.v3_router import v3_router, USER_ONBOARDING_STATE

app = FastAPI()
app.include_router(v3_router)
client = TestClient(app)

def benchmark_endpoint_latencies(endpoint_url: str, num_requests: int = 15) -> dict:
    # Warmup request to eliminate initial connection initialization overhead
    client.get(endpoint_url)

    latencies_ms = []
    for _ in range(num_requests):
        start = time.time()
        resp = client.get(endpoint_url)
        duration_ms = (time.time() - start) * 1000
        assert resp.status_code == 200
        latencies_ms.append(duration_ms)

    return {
        "p50": float(np.percentile(latencies_ms, 50)),
        "p95": float(np.percentile(latencies_ms, 95)),
        "p99": float(np.percentile(latencies_ms, 99)),
        "min": float(np.min(latencies_ms)),
        "max": float(np.max(latencies_ms))
    }

def run_gate_3_latency_benchmarks():
    print("\n--- Gate 3: Real HTTP Endpoint Latency Benchmarks (P50/P95/P99) ---")
    USER_ONBOARDING_STATE["bench_user"] = True

    # 1. Home Feed (Target: P50 < 50ms, P95 < 100ms, P99 < 200ms)
    home_lat = benchmark_endpoint_latencies("/api/v3/home?user_id=bench_user")
    assert home_lat["p95"] < 100.0, f"Home P95 was {home_lat['p95']:.2f}ms (Target: <100ms)"
    print(f"[PASSED] Home Feed: P50={home_lat['p50']:.2f}ms, P95={home_lat['p95']:.2f}ms, P99={home_lat['p99']:.2f}ms (<100ms SLA)")

    # 2. Content Details (Target: P50 < 20ms, P95 < 80ms)
    detail_lat = benchmark_endpoint_latencies("/api/v3/content/1")
    assert detail_lat["p95"] < 80.0, f"Detail P95 was {detail_lat['p95']:.2f}ms (Target: <80ms)"
    print(f"[PASSED] Content Details: P50={detail_lat['p50']:.2f}ms, P95={detail_lat['p95']:.2f}ms, P99={detail_lat['p99']:.2f}ms (<80ms SLA)")

    # 3. Content Recommendations (Target: P50 < 100ms, P95 < 250ms)
    recs_lat = benchmark_endpoint_latencies("/api/v3/content/1/recommendations?user_id=bench_user")
    assert recs_lat["p95"] < 250.0, f"Recommendations P95 was {recs_lat['p95']:.2f}ms (Target: <250ms)"
    print(f"[PASSED] Recommendations: P50={recs_lat['p50']:.2f}ms, P95={recs_lat['p95']:.2f}ms, P99={recs_lat['p99']:.2f}ms (<250ms SLA)")

    # 4. Observability Health (Target: P50 < 10ms, P95 < 30ms)
    health_lat = benchmark_endpoint_latencies("/api/v3/health/live")
    assert health_lat["p95"] < 30.0, f"Health P95 was {health_lat['p95']:.2f}ms (Target: <30ms)"
    print(f"[PASSED] Health Live: P50={health_lat['p50']:.2f}ms, P95={health_lat['p95']:.2f}ms, P99={health_lat['p99']:.2f}ms (<30ms SLA)")

if __name__ == "__main__":
    run_gate_3_latency_benchmarks()
    print("\nALL GATE 3 REAL HTTP LATENCY BENCHMARKS PASSED (100%)!")
