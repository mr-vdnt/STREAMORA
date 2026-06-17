"""
AURORA AI - Feature Store

Redis-backed real-time feature store for user profiles.
Uses fakeredis for local development (swap to real Redis in production).

Stores per-user:
  - Total event counts by type (views, clicks, purchases)
  - Recently interacted item IDs (sliding window)
  - Real-time interest scores per genre
  - Session metadata (last active, device, etc.)
"""

import json
import time
import fakeredis

# Use fakeredis for local dev; swap to redis.Redis(host=...) for production
_redis = fakeredis.FakeRedis(decode_responses=True)


def get_redis():
    return _redis


class FeatureStore:
    """Real-time user feature store backed by Redis."""

    def __init__(self, redis_client=None):
        self.r = redis_client or _redis

    # ── Write Operations ────────────────────────────────────────────

    def record_event(self, user_id: int, event_type: str, item_id: int, metadata: dict = None):
        """
        Update user features based on an incoming event.
        Called by the stream processor after consuming an event.
        """
        user_key = f"user:{user_id}"
        now = time.time()

        # 1. Increment event counter
        self.r.hincrby(user_key, f"count:{event_type}", 1)
        self.r.hincrby(user_key, "total_events", 1)

        # 2. Track recently interacted items (keep last 50)
        recent_key = f"user:{user_id}:recent_items"
        self.r.lpush(recent_key, item_id)
        self.r.ltrim(recent_key, 0, 49)

        # 3. Update genre interest scores if metadata contains genre
        if metadata and "genre" in metadata:
            genre = metadata["genre"]
            # Weighted scoring: purchase=5, click=2, view=1
            weight = {"purchase": 5, "click": 2, "view": 1}.get(event_type, 1)
            self.r.hincrbyfloat(user_key, f"genre:{genre}", weight)

        # 4. Update session metadata
        self.r.hset(user_key, "last_active", now)
        self.r.hset(user_key, "last_event_type", event_type)
        self.r.hset(user_key, "last_item_id", item_id)

        if metadata:
            if "device" in metadata:
                self.r.hset(user_key, "device", metadata["device"])
            if "session_id" in metadata:
                self.r.hset(user_key, "session_id", metadata["session_id"])

    # ── Read Operations ─────────────────────────────────────────────

    def get_user_profile(self, user_id: int) -> dict:
        """Get complete real-time user profile."""
        user_key = f"user:{user_id}"
        raw = self.r.hgetall(user_key)

        if not raw:
            return {"user_id": user_id, "exists": False}

        # Parse into structured profile
        profile = {
            "user_id": user_id,
            "exists": True,
            "total_events": int(raw.get("total_events", 0)),
            "event_counts": {},
            "genre_scores": {},
            "last_active": float(raw.get("last_active", 0)),
            "last_event_type": raw.get("last_event_type", ""),
            "last_item_id": int(raw.get("last_item_id", 0)),
            "device": raw.get("device", "unknown"),
        }

        for k, v in raw.items():
            if k.startswith("count:"):
                profile["event_counts"][k.replace("count:", "")] = int(v)
            elif k.startswith("genre:"):
                profile["genre_scores"][k.replace("genre:", "")] = float(v)

        return profile

    def get_recent_items(self, user_id: int, limit: int = 20) -> list[int]:
        """Get recently interacted item IDs."""
        recent_key = f"user:{user_id}:recent_items"
        items = self.r.lrange(recent_key, 0, limit - 1)
        return [int(i) for i in items]

    def get_top_genres(self, user_id: int, top_k: int = 5) -> list[tuple[str, float]]:
        """Get user's top genre interests, sorted by score."""
        profile = self.get_user_profile(user_id)
        genres = profile.get("genre_scores", {})
        sorted_genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)
        return sorted_genres[:top_k]

    # ── Stats ───────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get feature store stats."""
        keys = list(self.r.scan_iter("user:*"))
        user_keys = set()
        for k in keys:
            parts = k.split(":")
            if len(parts) >= 2:
                user_keys.add(parts[1])
        return {
            "total_user_profiles": len(user_keys),
            "total_redis_keys": len(keys),
        }


# Singleton
feature_store = FeatureStore()
