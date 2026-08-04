from __future__ import annotations

class CacheKeyBuilder:
    """Canonical cache key namespace builder for home feed, hero banner, search, and recommendations."""

    @staticmethod
    def home_feed(user_id: str) -> str:
        return f"streamora:home:{user_id}"

    @staticmethod
    def hero_banner(user_id: str) -> str:
        return f"streamora:hero:{user_id}"

    @staticmethod
    def search_plan(query_hash: str) -> str:
        return f"streamora:search:plan:{query_hash}"

    @staticmethod
    def discovery_hub(hub_slug: str) -> str:
        return f"streamora:discovery:hub:{hub_slug}"

    @staticmethod
    def content_details(content_id: int) -> str:
        return f"streamora:content:{content_id}"
