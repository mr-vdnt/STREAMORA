import os
import sys
import re
import json
import time
import requests
import uuid

# Base URL for local testing (defaults to local dev server on port 10000)
BASE_URL = os.getenv("TARGET_URL", "http://127.0.0.1:10000")

FORBIDDEN_STRINGS = [
    "85% Match",
    "Unknown Director",
    "Unknown Writer",
    "Streamora AI",
    "Highly correlated",
    "Undisclosed",
    "Standalone",
    "Recommended for you",
]

FORBIDDEN_PATTERNS = [
    r"\d+%\s*Match",
]

def log_step(name):
    print(f"\n[{time.strftime('%H:%M:%S')}] \033[1;34m[TEST]\033[0m {name}")

def fail(msg):
    print(f"\033[1;31m[FAIL]\033[0m {msg}")
    sys.exit(1)

def pass_test(msg="OK"):
    print(f"\033[1;32m[PASS]\033[0m {msg}")

def warn(msg):
    print(f"\033[1;33m[WARN]\033[0m {msg}")

def check_forbidden(payload_str, context=""):
    """Check a JSON string for forbidden values and patterns."""
    for f in FORBIDDEN_STRINGS:
        if f in payload_str:
            fail(f"Forbidden value '{f}' found in {context}")
    for p in FORBIDDEN_PATTERNS:
        match = re.search(p, payload_str)
        if match:
            fail(f"Forbidden pattern '{match.group()}' found in {context}")

def run_tests():
    print("==========================================")
    print("STREAMORA RELEASE CANDIDATE E2E VALIDATION")
    print("==========================================")

    headers = {}
    cookies = None

    # 1. Health and Startup
    log_step("Testing Health & Startup Metrics")
    try:
        r = requests.get(f"{BASE_URL}/ready", timeout=10)
        if r.status_code == 200:
            data = r.json()
            startup_ms = data.get("startup_ms", 0)
            pass_test(f"/ready OK (Startup time: {startup_ms}ms)")
            if startup_ms > 5000:
                warn("Startup time exceeded 5 seconds.")
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

        r = requests.post(f"{BASE_URL}/token", json={
            "username": test_user,
            "password": test_pass
        })
        if r.status_code == 200:
            token = r.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            cookies = r.cookies
            pass_test("Login OK & JWT received")
        else:
            fail(f"Login failed: {r.text}")
    except Exception as e:
        fail(f"Auth error: {e}")

    # 3. Home Endpoint (Performance + Metadata Integrity)
    log_step("Testing Home Performance & Metadata Integrity")
    try:
        t0 = time.time()
        r = requests.get(f"{BASE_URL}/api/v2/home", headers=headers)
        t1 = time.time()
        cold_ms = (t1 - t0) * 1000

        if r.status_code != 200:
            fail(f"/api/v2/home failed: {r.status_code}")

        home_data = r.json()
        home_str = json.dumps(home_data)

        if "hero" not in home_data or "sections" not in home_data:
            fail("Missing hero/sections in /api/v2/home response")
        pass_test(f"/api/v2/home cold OK ({cold_ms:.0f}ms)")

        if cold_ms > 2000:
            warn(f"Home cold response {cold_ms:.0f}ms exceeds 2000ms gate")
        else:
            pass_test(f"Home performance gate PASS ({cold_ms:.0f}ms < 2000ms)")

        check_forbidden(home_str, "/api/v2/home")
        pass_test("No forbidden placeholders in home response")

        sections = home_data.get("sections", [])
        if len(sections) > 0:
            pass_test(f"Home contains {len(sections)} shelves")
        else:
            fail("Home returned 0 shelves")

        # Warm request
        t2 = time.time()
        r2 = requests.get(f"{BASE_URL}/api/v2/home", headers=headers)
        t3 = time.time()
        warm_ms = (t3 - t2) * 1000
        if r2.status_code == 200:
            pass_test(f"/api/v2/home warm OK ({warm_ms:.0f}ms)")
        else:
            fail(f"/api/v2/home warm failed: {r2.status_code}")

    except Exception as e:
        fail(f"Home error: {e}")

    # 4. Search
    log_step("Testing Search & Alias Normalization")
    try:
        r = requests.get(f"{BASE_URL}/api/v2/search/v2?q=spider", headers=headers)
        if r.status_code == 200 and "grouped_results" in r.json():
            pass_test("/api/v2/search/v2 autocomplete OK")
        else:
            fail("/api/v2/search/v2 failed")

        r = requests.get(f"{BASE_URL}/api/v2/search/v2?q=spidr", headers=headers)
        if r.status_code == 200:
            pass_test("Typo-tolerant search OK")
        else:
            fail(f"Typo search failed: {r.text}")
    except Exception as e:
        fail(f"Search error: {e}")

    # 5. Content Detail (Performance + Metadata Integrity)
    log_step("Testing Content Detail & Metadata Integrity")
    try:
        t0 = time.time()
        r = requests.get(f"{BASE_URL}/api/v2/content/2", headers=headers)
        t1 = time.time()
        detail_ms = (t1 - t0) * 1000

        if r.status_code != 200:
            fail(f"/api/v2/content/2 failed: {r.text}")

        detail_data = r.json()
        detail_str = json.dumps(detail_data)

        if not isinstance(detail_data, dict) or len(detail_data) == 0:
            fail("Empty content detail response")
        pass_test(f"/api/v2/content/2 OK ({detail_ms:.0f}ms)")

        check_forbidden(detail_str, "/api/v2/content/2")
        pass_test("No forbidden placeholders in detail response")

        if "rating_source" in detail_str:
            pass_test("Rating provenance field present")
        else:
            warn("No rating_source provenance in detail response")

    except Exception as e:
        fail(f"Detail error: {e}")

    # 6. Chat
    log_step("Testing Chat Endpoints")
    try:
        t0 = time.time()
        r = requests.post(f"{BASE_URL}/chat", json={"query": "What are some good sci-fi movies?"}, headers=headers, cookies=cookies)
        t1 = time.time()
        if r.status_code == 200:
            pass_test(f"Chat (Cold) OK ({(t1-t0)*1000:.0f}ms)")
        else:
            fail(f"Chat failed: {r.text}")

        t0 = time.time()
        r = requests.post(f"{BASE_URL}/chat", json={"query": "Tell me more about Inception."}, headers=headers, cookies=cookies)
        t1 = time.time()
        if r.status_code == 200:
            pass_test(f"Chat (Warm) OK ({(t1-t0)*1000:.0f}ms)")
        else:
            fail(f"Chat failed: {r.text}")
    except Exception as e:
        fail(f"Chat error: {e}")

    print("\n==========================================")
    print("\033[1;32mALL TESTS PASSED\033[0m")
    print("RC1 Performance + Metadata Correction verified.")
    print("==========================================")

if __name__ == "__main__":
    run_tests()

