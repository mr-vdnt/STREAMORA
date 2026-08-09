import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/streamora.db')

def get_db_connection():
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        display_name TEXT DEFAULT 'Explorer',
        avatar_url TEXT DEFAULT '',
        role TEXT DEFAULT 'Standard',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Watchlist table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_watchlists (
        user_id INTEGER PRIMARY KEY,
        items TEXT DEFAULT '[]',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    # History table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_history (
        user_id INTEGER PRIMARY KEY,
        items TEXT DEFAULT '[]',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    # Revoked tokens table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS revoked_tokens (
        token TEXT PRIMARY KEY,
        revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # User Preferences & Onboarding Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_preferences (
        user_id INTEGER PRIMARY KEY,
        selected_categories TEXT DEFAULT '[]',
        disliked_categories TEXT DEFAULT '[]',
        affinity_weights TEXT DEFAULT '{}',
        onboarding_completed INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    conn.commit()
    conn.close()

def revoke_token(token: str):
    """Revokes a JWT token by adding it to the blocklist."""
    if not token:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO revoked_tokens (token) VALUES (?)", (token,))
    conn.commit()
    conn.close()

def is_token_revoked(token: str) -> bool:
    """Checks if a JWT token has been revoked."""
    if not token:
        return True
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM revoked_tokens WHERE token = ?", (token,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def create_user(username: str, email: str, hashed_password: str, display_name: str) -> Optional[int]:
    """Creates a new user and returns their ID. Returns None if username/email exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, hashed_password, display_name) VALUES (?, ?, ?, ?)",
            (username, email, hashed_password, display_name)
        )
        user_id = cursor.lastrowid
        
        # Initialize empty watchlist and history
        cursor.execute("INSERT INTO user_watchlists (user_id, items) VALUES (?, '[]')", (user_id,))
        cursor.execute("INSERT INTO user_history (user_id, items) VALUES (?, '[]')", (user_id,))
        
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Retrieves a user by username."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a user by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def update_user_profile(user_id: int, display_name: str, email: str) -> bool:
    """Updates user profile information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET display_name = ?, email = ? WHERE id = ?",
            (display_name, email, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def save_watchlist(user_id: int, items: list):
    """Saves a user's watchlist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    items_json = json.dumps(items)
    cursor.execute(
        "UPDATE user_watchlists SET items = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
        (items_json, user_id)
    )
    if cursor.rowcount == 0:
        cursor.execute("INSERT INTO user_watchlists (user_id, items) VALUES (?, ?)", (user_id, items_json))
    conn.commit()
    conn.close()

def get_watchlist(user_id: int) -> list:
    """Retrieves a user's watchlist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT items FROM user_watchlists WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row['items']:
        try:
            return json.loads(row['items'])
        except:
            pass
    return []

def save_history(user_id: int, items: list):
    """Saves a user's watch history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    items_json = json.dumps(items)
    cursor.execute(
        "UPDATE user_history SET items = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
        (items_json, user_id)
    )
    if cursor.rowcount == 0:
        cursor.execute("INSERT INTO user_history (user_id, items) VALUES (?, ?)", (user_id, items_json))
    conn.commit()
    conn.close()

def get_history(user_id: int) -> list:
    """Retrieves a user's watch history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT items FROM user_history WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row['items']:
        try:
            return json.loads(row['items'])
        except:
            pass
    return []

def save_user_onboarding(user_id: int, selected_categories: list, disliked_categories: list = None) -> dict:
    """Saves user onboarding selections and initializes affinity weights."""
    init_db()
    disliked_categories = disliked_categories or []
    
    # Initialize affinity weights for selected categories (0.85 base weight)
    affinity_weights = {cat: 0.85 for cat in selected_categories}
    for cat in disliked_categories:
        affinity_weights[cat] = -1.0

    conn = get_db_connection()
    cursor = conn.cursor()
    sel_json = json.dumps(selected_categories)
    dis_json = json.dumps(disliked_categories)
    weights_json = json.dumps(affinity_weights)
    
    cursor.execute(
        """UPDATE user_preferences 
           SET selected_categories = ?, disliked_categories = ?, affinity_weights = ?, onboarding_completed = 1, updated_at = CURRENT_TIMESTAMP 
           WHERE user_id = ?""",
        (sel_json, dis_json, weights_json, user_id)
    )
    if cursor.rowcount == 0:
        cursor.execute(
            """INSERT INTO user_preferences (user_id, selected_categories, disliked_categories, affinity_weights, onboarding_completed) 
               VALUES (?, ?, ?, ?, 1)""",
            (user_id, sel_json, dis_json, weights_json)
        )
    conn.commit()
    conn.close()
    
    return {
        "user_id": user_id,
        "selected_categories": selected_categories,
        "disliked_categories": disliked_categories,
        "affinity_weights": affinity_weights,
        "onboarding_completed": True
    }

def get_user_preferences(user_id: int) -> dict:
    """Retrieves a user's preferences and affinity weights."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "user_id": user_id,
            "selected_categories": json.loads(row['selected_categories'] or '[]'),
            "disliked_categories": json.loads(row['disliked_categories'] or '[]'),
            "affinity_weights": json.loads(row['affinity_weights'] or '{}'),
            "onboarding_completed": bool(row['onboarding_completed'])
        }
    return {
        "user_id": user_id,
        "selected_categories": [],
        "disliked_categories": [],
        "affinity_weights": {},
        "onboarding_completed": False
    }

EVENT_WEIGHTS = {
    "impression": 0.01,
    "click": 0.10,
    "detail_dwell": 0.15,
    "trailer_watched": 0.20,
    "playback_started": 0.30,
    "fifty_percent_watched": 0.50,
    "completed": 0.75,
    "watchlist_added": 0.60,
    "explicit_dislike": -1.00
}

def record_user_event(user_id: int, event_type: str, categories: list) -> dict:
    """Updates user affinity weights using event signals with temporal decay."""
    delta = EVENT_WEIGHTS.get(event_type.lower(), 0.05)
    prefs = get_user_preferences(user_id)
    weights = prefs.get("affinity_weights", {})
    
    # Apply lightweight decay factor (0.98) to existing weights
    for cat in weights:
        if weights[cat] > 0:
            weights[cat] *= 0.98

    # Apply new event delta
    for cat in categories:
        current = weights.get(cat, 0.5)
        weights[cat] = round(max(-1.0, min(1.0, current + delta)), 3)

    conn = get_db_connection()
    cursor = conn.cursor()
    weights_json = json.dumps(weights)
    cursor.execute(
        "UPDATE user_preferences SET affinity_weights = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
        (weights_json, user_id)
    )
    conn.commit()
    conn.close()
    
    prefs["affinity_weights"] = weights
    return prefs

