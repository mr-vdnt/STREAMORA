import sqlite3
import json
import threading
from queue import Queue
from typing import Dict, Any

class EventPipeline:
    """
    Asynchronous event pipeline for recording analytics.
    Events -> Queue -> SQLite Background Writer
    """
    _queue = Queue()
    _worker_thread = None
    _db_path = "data/analytics.db"
    
    @classmethod
    def _init_db(cls):
        conn = sqlite3.connect(cls._db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS search_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                user_id INTEGER,
                timestamp TEXT,
                query TEXT,
                latency REAL,
                results INTEGER,
                clicked_movie INTEGER,
                session_id TEXT,
                device TEXT
            )
        ''')
        conn.commit()
        conn.close()

    @classmethod
    def _worker_loop(cls):
        cls._init_db()
        while True:
            event = cls._queue.get()
            if event is None:
                break
                
            try:
                conn = sqlite3.connect(cls._db_path)
                c = conn.cursor()
                if event.get("event_type") == "search":
                    c.execute('''
                        INSERT INTO search_events 
                        (event_type, user_id, timestamp, query, latency, results, clicked_movie, session_id, device)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        event.get("event_type"),
                        event.get("user_id"),
                        event.get("timestamp"),
                        event.get("query"),
                        event.get("latency"),
                        event.get("results"),
                        event.get("clicked_movie"),
                        event.get("session_id"),
                        event.get("device")
                    ))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"[Analytics] Failed to write event: {e}")
            finally:
                cls._queue.task_done()

    @classmethod
    def start(cls):
        if cls._worker_thread is None:
            cls._worker_thread = threading.Thread(target=cls._worker_loop, daemon=True)
            cls._worker_thread.start()

    @classmethod
    def log_search(cls, event: Dict[str, Any]):
        cls.start()
        cls._queue.put(event)
