import os
import sys
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ["ENVIRONMENT"] = "test"

from fastapi.testclient import TestClient
from services.agent.main import app

def test_full_browser_auth_flow():
    client = TestClient(app)
    
    unique_suffix = uuid.uuid4().hex[:6]
    username = f"user_{unique_suffix}"
    email = f"user_{unique_suffix}@streamora.ai"
    password = "SecurePassword123!"
    
    print(f"--- STARTING BROWSER-STYLE AUTH FLOW FOR '{username}' ---")
    
    # Step 1: Initial CSRF fetch
    r1 = client.get("/csrf-token")
    assert r1.status_code == 200
    csrf_token = r1.json()["csrf_token"]
    print("1. Fetched initial CSRF token.")
    
    # Step 2: Register
    r2 = client.post("/register", json={
        "username": username,
        "email": email,
        "password": password,
        "display_name": f"User {unique_suffix}"
    })
    assert r2.status_code == 200, f"Register failed: {r2.text}"
    print("2. Registered new user successfully.")
    
    # Step 3: Login
    r3 = client.post("/token", json={
        "username": username,
        "password": password
    })
    assert r3.status_code == 200, f"Login immediately after register failed: {r3.text}"
    print("3. Logged in immediately after register (cookie set).")
    
    # Step 4: Verify Session via /me
    r4 = client.get("/me")
    assert r4.status_code == 200
    me_data = r4.json()
    assert me_data["username"] == username
    print(f"4. Checked /me: Logged in as '{me_data['username']}'.")
    
    # Step 5: Refresh browser / Refresh Token
    csrf_token = client.cookies.get("csrf_token")
    r5 = client.post("/auth/refresh", headers={"x-csrf-token": csrf_token})
    assert r5.status_code == 200
    print("5. Token rotation / refresh succeeded.")
    
    # Step 6: Still Logged In
    r6 = client.get("/me")
    assert r6.status_code == 200
    print("6. User still logged in after refresh.")
    
    # Step 7: Logout
    csrf_token = client.cookies.get("csrf_token")
    r7 = client.post("/logout", headers={"x-csrf-token": csrf_token})
    assert r7.status_code == 200
    print("7. Logged out.")
    
    # Step 8: 401 on /me
    r8 = client.get("/me")
    assert r8.status_code == 401
    print("8. Verified 401 Unauthorized after logout.")
    
    # Step 9: Login Again
    r9 = client.post("/token", json={
        "username": username,
        "password": password
    })
    assert r9.status_code == 200
    print("9. Logged in again with same credentials successfully!")
    
    print("--- ALL 9 BROWSER AUTHENTICATION STEPS VERIFIED 100% CLEAN ---")

if __name__ == '__main__':
    test_full_browser_auth_flow()
