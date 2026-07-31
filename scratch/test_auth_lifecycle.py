import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set ENVIRONMENT=test to skip background warmup in lifespan
os.environ["ENVIRONMENT"] = "test"

from fastapi.testclient import TestClient
from services.agent.main import app

def test_auth_lifecycle():
    client = TestClient(app)
    
    print("1. Testing GET /csrf-token...")
    res = client.get("/csrf-token")
    assert res.status_code == 200, f"Failed csrf-token: {res.text}"
    csrf_data = res.json()
    csrf_token = csrf_data.get("csrf_token")
    assert csrf_token is not None, "CSRF token missing"
    print("   CSRF token retrieved successfully.")
    
    headers = {"x-csrf-token": csrf_token}
    
    print("2. Testing POST /register...")
    test_user = {
        "username": "testuser_auth",
        "email": "testuser_auth@example.com",
        "password": "Password123!",
        "display_name": "Test User Auth"
    }
    # Note: /register bypasses CSRF check in AuthMiddleware
    res = client.post("/register", json=test_user)
    print(f"   Register response status: {res.status_code}, body: {res.text}")
    assert res.status_code in [200, 400], "Register returned unexpected status"
    
    print("3. Testing POST /token (login)...")
    login_data = {
        "username": "testuser_auth",
        "password": "Password123!"
    }
    res = client.post("/token", json=login_data)
    assert res.status_code == 200, f"Login failed: {res.text}"
    login_res = res.json()
    assert login_res.get("status") == "success", "Login failed"
    print("   Login success!")
    
    print("4. Testing GET /me (authenticated)...")
    res = client.get("/me")
    assert res.status_code == 200, f"GET /me failed: {res.text}"
    user_info = res.json()
    print(f"   Logged in user: {user_info.get('username')} (Role: {user_info.get('role')})")
    
    # Refresh CSRF header from client cookies since set_auth_cookies updated the csrf_token cookie on login
    csrf_token = client.cookies.get("csrf_token")
    headers = {"x-csrf-token": csrf_token}
    
    print("5. Testing POST /auth/refresh...")
    res = client.post("/auth/refresh", headers=headers)
    assert res.status_code == 200, f"Refresh token failed: {res.text}"
    print("   Token refreshed successfully.")
    
    # Refresh CSRF header again after /auth/refresh set new cookies
    csrf_token = client.cookies.get("csrf_token")
    headers = {"x-csrf-token": csrf_token}
    
    print("6. Testing POST /logout...")
    res = client.post("/logout", headers=headers)
    assert res.status_code == 200, f"Logout failed: {res.text}"
    print("   Logout success!")
    
    print("7. Testing GET /me after logout (should fail 401)...")
    res = client.get("/me")
    assert res.status_code == 401, f"Expected 401 after logout, got {res.status_code}"
    print("   Unauthenticated access properly blocked.")
    
    print("ALL AUTHENTICATION LIFECYCLE TESTS PASSED!")

if __name__ == '__main__':
    test_auth_lifecycle()
