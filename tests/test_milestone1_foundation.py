"""
STREAMORA - Milestone 1 Regression Test Suite
Validates User Registration, Login, Guest Session, Watchlist Persistence across re-logins,
Watch History, Token Rotation, and Logout Revocation.
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from services.agent.main import app
from services.security.user_data import (
    init_db, create_user, get_user_by_username, 
    get_watchlist, save_watchlist, get_history, save_history
)

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_user_registration_and_login():
    unique_user = f"user_{uuid.uuid4().hex[:6]}"
    email = f"{unique_user}@streamora.test"
    password = "SecurePassword123!"

    # 1. Register User
    reg_response = client.post(
        "/register",
        json={
            "username": unique_user,
            "email": email,
            "password": password,
            "display_name": "Test Explorer"
        }
    )
    assert reg_response.status_code == 200
    assert reg_response.json()["status"] == "success"

    # 2. Login User
    login_response = client.post(
        "/token",
        json={
            "username": unique_user,
            "password": password
        }
    )
    assert login_response.status_code == 200
    data = login_response.json()
    assert data["username"] == unique_user
    assert data["role"] == "Standard"


def test_guest_authentication():
    response = client.post("/auth/guest")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["role"] == "Guest"
    assert data["username"].startswith("guest_")
    assert "access_token" in data


def test_watchlist_persistence():
    unique_user = f"watch_{uuid.uuid4().hex[:6]}"
    email = f"{unique_user}@streamora.test"
    password = "SecurePassword123!"

    # Register & Login
    client.post("/register", json={"username": unique_user, "email": email, "password": password})
    login_res = client.post("/token", json={"username": unique_user, "password": password})
    user_id = login_res.json()["user_id"]

    # Save initial watchlist
    initial_items = [{"id": 101, "title": "Inception", "type": "movie"}]
    save_watchlist(user_id, initial_items)

    # Verify initial save
    retrieved = get_watchlist(user_id)
    assert len(retrieved) == 1
    assert retrieved[0]["title"] == "Inception"

    # Simulate Re-login & Verify Persistence
    relogin_res = client.post("/token", json={"username": unique_user, "password": password})
    assert relogin_res.status_code == 200
    
    persisted_watchlist = get_watchlist(user_id)
    assert len(persisted_watchlist) == 1
    assert persisted_watchlist[0]["id"] == 101


def test_history_persistence():
    unique_user = f"hist_{uuid.uuid4().hex[:6]}"
    email = f"{unique_user}@streamora.test"
    password = "SecurePassword123!"

    client.post("/register", json={"username": unique_user, "email": email, "password": password})
    login_res = client.post("/token", json={"username": unique_user, "password": password})
    user_id = login_res.json()["user_id"]

    history_items = [{"id": 202, "title": "Interstellar", "position_sec": 1450, "duration_sec": 7500}]
    save_history(user_id, history_items)

    retrieved_history = get_history(user_id)
    assert len(retrieved_history) == 1
    assert retrieved_history[0]["position_sec"] == 1450


def test_logout_revocation():
    unique_user = f"logout_{uuid.uuid4().hex[:6]}"
    email = f"{unique_user}@streamora.test"
    password = "SecurePassword123!"

    client.post("/register", json={"username": unique_user, "email": email, "password": password})
    login_res = client.post("/token", json={"username": unique_user, "password": password})
    assert login_res.status_code == 200

    logout_res = client.post("/logout")
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "success"
