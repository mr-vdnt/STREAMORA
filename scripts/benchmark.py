import time
import requests
import json
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor

API_URL = "http://localhost:8000"

def run_health_benchmark(num_requests: int = 100):
    start = time.time()
    latencies = []
    
    for _ in range(num_requests):
        t0 = time.time()
        res = requests.get(f"{API_URL}/health")
        latencies.append((time.time() - t0) * 1000)
        
    total_time = time.time() - start
    
    print(f"\n--- Health Check Benchmark ({num_requests} requests) ---")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Avg Latency: {statistics.mean(latencies):.2f}ms")
    print(f"P95 Latency: {statistics.quantiles(latencies, n=20)[18]:.2f}ms")

def run_recommendation_benchmark(num_requests: int = 20, concurrency: int = 2):
    print(f"\n--- Recommendation Benchmark ({num_requests} requests, concurrency {concurrency}) ---")
    latencies = []
    
    payload = {
        "query": "I want a dark sci-fi movie about AI",
        "user_id": "42"
    }
    
    def req():
        t0 = time.time()
        res = requests.post(f"{API_URL}/recommendations/", json=payload, headers={"x-session-id": "bench-123"})
        res.raise_for_status()
        return (time.time() - t0) * 1000

    start = time.time()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(req) for _ in range(num_requests)]
        for f in futures:
            try:
                latencies.append(f.result())
            except Exception as e:
                print(f"Request failed: {e}")
                
    total_time = time.time() - start
    
    if latencies:
        print(f"Total Time: {total_time:.2f}s")
        print(f"Avg Latency: {statistics.mean(latencies):.2f}ms")
        if len(latencies) >= 20:
            print(f"P95 Latency: {statistics.quantiles(latencies, n=20)[18]:.2f}ms")
        print(f"Throughput: {len(latencies) / total_time:.2f} req/s")

if __name__ == "__main__":
    print("Waiting for server to start...")
    try:
        requests.get(f"{API_URL}/health")
    except Exception:
        print("Error: Make sure the FastAPI server is running on localhost:8000")
        print("Run: uvicorn api.app:app --reload")
        sys.exit(1)
        
    run_health_benchmark()
    run_recommendation_benchmark()
