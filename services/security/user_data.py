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
    
    conn.commit()
    conn.close()

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
