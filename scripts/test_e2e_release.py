import os
import sys
import time
import requests
import uuid

# Base URL for local testing
BASE_URL = "http://127.0.0.1:10000"

def log_step(name):
    print(f"\n[{time.strftime('%H:%M:%S')}] \033[1;34m[TEST]\033[0m {name}")

def fail(msg):
    print(f"\033[1;31m[FAIL]\033[0m {msg}")
    sys.exit(1)

def pass_test(msg="OK"):
    print(f"\033[1;32m[PASS]\033[0m {msg}")

def run_tests():
    print("==========================================")
    print("STREAMORA RELEASE CANDIDATE E2E VALIDATION")
    print("==========================================")
    
    # 1. Health and Startup
    log_step("Testing Health & Startup Metrics")
    try:
        r = requests.get(f"{BASE_URL}/ready", timeout=2)
        if r.status_code == 200:
            data = r.json()
            startup_ms = data.get("startup_ms", 0)
            pass_test(f"/ready OK (Startup time: {startup_ms}ms)")
            if startup_ms > 5000:
                print("\033[1;33m[WARN]\033[0m Startup time exceeded 5 seconds.")
        else:
            fail(f"/ready returned {r.status_code}")
            
        r = requests.get(f"{BASE_URL}/health/deep", timeout=10)
        if r.status_code == 200:
            data = r.json()
            pass_test(f"/health/deep OK (LLM Loaded: {data.get('llm_loaded')})")
        else:
            fail(f"/health/deep returned {r.status_code}")
    except Exception as e:
        fail(f"Could not connect to backend: {e}")

    # 2. Authentication
    log_step("Testing Authentication Flow")
    test_user = f"testuser_{uuid.uuid4().hex[:6]}"
    test_pass = "password123"
    
    try:
        # Register
        r = requests.post(f"{BASE_URL}/register", json={
            "username": test_user,
            "email": f"{test_user}@test.com",
            "password": test_pass,
            "display_name": "Test User"
        })
        if r.status_code == 200:
            pass_test("Registration OK")
        else:
            fail(f"Registration failed: {r.text}")
            
        # Login
        r = requests.post(f"{BASE_URL}/token", data={
            "username": test_user,
            "password": test_pass
        })
        if r.status_code == 200:
            token = r.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            pass_test("Login OK & JWT received")
        else:
            fail(f"Login failed: {r.text}")
    except Exception as e:
        fail(f"Auth error: {e}")

    # 3. Discovery & Home
    log_step("Testing Discovery / Home Endpoints")
    try:
        t0 = time.time()
        r = requests.get(f"{BASE_URL}/home", headers=headers)
        t1 = time.time()
        if r.status_code == 200:
            data = r.json()
            # Assert schema
            if "hero" in data and "sections" in data:
                pass_test(f"/home aggregated payload OK ({(t1-t0)*1000:.0f}ms)")
            else:
                fail("Missing discovery/platform in /home response")
        else:
            fail(f"/home failed: {r.status_code}")
            
        # Discover specific genre
        r = requests.get(f"{BASE_URL}/discover?genre=Action&limit=5", headers=headers)
        if r.status_code == 200 and len(r.json().get("results", [])) > 0:
            pass_test("/discover with genre OK")
        else:
            fail("/discover failed")
    except Exception as e:
        fail(f"Discovery error: {e}")

    # 4. Item Details Routing
    log_step("Testing Item Details Aggregation")
    try:
        r = requests.get(f"{BASE_URL}/api/item/movie/1", headers=headers)
        if r.status_code == 200:
            data = r.json()
            if "movie" in data and "similar" in data:
                pass_test("/api/item/movie/1 OK")
            else:
                fail("Missing sections in item details response")
        else:
            fail(f"/api/item/movie/1 failed: {r.text}")
    except Exception as e:
        fail(f"Item details error: {e}")

    # 5. Semantic Search & Chat (Testing Cold Start)
    log_step("Testing Semantic Search & AI Chat")
    try:
        r = requests.post(f"{BASE_URL}/search", json={"query": "batman"}, headers=headers)
        if r.status_code == 200:
            pass_test("Semantic search OK")
        else:
            fail(f"Search failed: {r.text}")
            
        # Cold Chat
        t0 = time.time()
        r = requests.post(f"{BASE_URL}/chat", json={"query": "What are some good sci-fi movies?"}, headers=headers)
        t1 = time.time()
        if r.status_code == 200:
            pass_test(f"Chat (Cold Load) OK ({(t1-t0)*1000:.0f}ms)")
        else:
            fail(f"Chat failed: {r.text}")
            
        # Warm Chat
        t0 = time.time()
        r = requests.post(f"{BASE_URL}/chat", json={"query": "Tell me more about Inception."}, headers=headers)
        t1 = time.time()
        if r.status_code == 200:
            pass_test(f"Chat (Warm) OK ({(t1-t0)*1000:.0f}ms)")
        else:
            fail(f"Chat failed: {r.text}")
            
    except Exception as e:
        fail(f"AI error: {e}")

    print("==========================================")
    print("\033[1;32mALL TESTS PASSED\033[0m")
    print("Release Candidate is ready for deployment.")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
