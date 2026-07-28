import time
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.discovery.home_service import HomeService

def test_perf():
    service = HomeService()
    
    # 1. Cold start
    t0 = time.time()
    payload = service.get_home_payload()
    t1 = time.time()
    cold_ms = int((t1 - t0) * 1000)
    print(f"Cold Start: {cold_ms}ms (Shelves: {len(payload.get('sections', []))})")
    
    # 2. Warm start
    t2 = time.time()
    payload2 = service.get_home_payload()
    t3 = time.time()
    warm_ms = int((t3 - t2) * 1000)
    print(f"Warm Start (Cached): {warm_ms}ms")
    
    if warm_ms > 300:
        print("FAIL: Cache took longer than 300ms")
    else:
        print("PASS: Cache response <300ms")

if __name__ == "__main__":
    test_perf()
