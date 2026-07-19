import sys
import os
import unittest
import string
import random
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.agent.main import app
from services.security.user_data import get_user_by_username
from services.agent.limiter import limiter

# Disable rate limiting for tests to prevent 429 Too Many Requests
limiter.enabled = False

class TestAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        # Create a test user for testing valid logins
        cls.test_username = "testuser_" + "".join(random.choices(string.ascii_lowercase, k=6))
        cls.test_password = "securepassword123"
        
        # Register the test user ONCE for the whole class
        response = cls.client.post("/register", json={
            "username": cls.test_username,
            "email": f"{cls.test_username}@example.com",
            "password": cls.test_password,
            "display_name": "Test User"
        })
        assert response.status_code in [200, 400], "Setup failed: Could not register test user"

    def test_a_login_valid_credentials(self):
        # Using a fresh client session for each test to clear cookies
        client = TestClient(app)
        response = client.post("/token", json={
            "username": self.test_username,
            "password": self.test_password
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("user_id", data)
        self.assertEqual(data["username"], self.test_username)
        
        # Verify HttpOnly Cookies were set
        cookies = response.cookies
        self.assertIn("access_token", cookies)
        self.assertIn("refresh_token", cookies)
        # Note: TestClient cookies may not expose httponly attribute directly easily,
        # but we can verify the cookies are present.

    def test_b_protected_route_without_cookie(self):
        client = TestClient(app)
        response = client.get("/me")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Not authenticated"})

    def test_c_protected_route_with_cookie(self):
        client = TestClient(app)
        # Login to get cookies
        client.post("/token", json={
            "username": self.test_username,
            "password": self.test_password
        })
        # Access protected route
        response = client.get("/me")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], self.test_username)

    def test_d_logout_clears_cookie(self):
        client = TestClient(app)
        # Login
        client.post("/token", json={
            "username": self.test_username,
            "password": self.test_password
        })
        # Logout
        logout_response = client.post("/logout")
        self.assertEqual(logout_response.status_code, 200)
        
        # Access protected route (should fail)
        response = client.get("/me")
        self.assertEqual(response.status_code, 401)

    def test_login_invalid_password(self):
        client = TestClient(app)
        response = client.post("/token", json={
            "username": self.test_username,
            "password": "wrongpassword"
        })
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Invalid username or password."})

    def test_login_unknown_username(self):
        client = TestClient(app)
        response = client.post("/token", json={
            "username": "unknown_user_12345",
            "password": "somepassword"
        })
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Invalid username or password."})
        
        # Verify the user was NOT auto-registered
        user = get_user_by_username("unknown_user_12345")
        self.assertIsNone(user, "User was auto-registered, which is a security vulnerability")

    def test_login_empty_username(self):
        client = TestClient(app)
        response = client.post("/token", json={
            "username": "",
            "password": "somepassword"
        })
        # FastAPI might return 422 for pydantic model failure or 401 depending on validation
        self.assertIn(response.status_code, [401, 422])

    def test_login_empty_password(self):
        client = TestClient(app)
        response = client.post("/token", json={
            "username": self.test_username,
            "password": ""
        })
        self.assertIn(response.status_code, [401, 422])

    def test_login_sql_injection(self):
        client = TestClient(app)
        sql_payloads = [
            "' OR '1'='1",
            "admin' --",
            "\" OR \"1\"=\"1",
            "'; DROP TABLE users; --"
        ]
        for payload in sql_payloads:
            response = client.post("/token", json={
                "username": payload,
                "password": payload
            })
            self.assertEqual(response.status_code, 401)

    def test_login_oversized_payload(self):
        client = TestClient(app)
        oversized_username = "A" * 10000
        response = client.post("/token", json={
            "username": oversized_username,
            "password": "password"
        })
        self.assertIn(response.status_code, [401, 413, 422])

    def test_login_unicode_usernames(self):
        client = TestClient(app)
        response = client.post("/token", json={
            "username": "ユーザー名",
            "password": "password123"
        })
        self.assertEqual(response.status_code, 401)

    def test_login_very_long_password(self):
        client = TestClient(app)
        very_long_password = "B" * 5000
        response = client.post("/token", json={
            "username": self.test_username,
            "password": very_long_password
        })
        self.assertEqual(response.status_code, 401)

if __name__ == "__main__":
    unittest.main()
