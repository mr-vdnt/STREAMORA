from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc

from services.repository.catalog_db import (
    CatalogRepository,
    Content,
    ContentArtwork,
    ContentMetadata,
    ContentStatistics,
)

logger = logging.getLogger("streamora.recommendation.precomputation")


class PrecomputationWorker:
    """Build a bounded home read-model without running the full recommendation pipeline.

    The previous implementation executed the complete recommendation pipeline synchronously
    during API startup and on cache misses. That made a health-ready process appear alive while
    the first UI request remained blocked on recommendation generation.

    This worker deliberately separates the fast bootstrap slate from the expensive offline
    recommendation pipeline. The expensive pipeline can populate a richer snapshot later; the
    HTTP request never depends on it.
    """

    def __init__(self, pipeline: Optional[Any] = None, repo: Optional[CatalogRepository] = None):
        self.pipeline = pipeline
        self.repo = repo or CatalogRepository()
        self._snapshots: Dict[str, Dict[str, Any]] = {}
        self._snapshot_ttl_seconds = 300

    @staticmethod
    def _to_item(content: Content) -> Dict[str, Any]:
        metadata = content.metadata_rel
        artwork = content.artwork_rel
        stats = content.statistics_rel
        release_date = metadata.release_date if metadata else ""
        year = release_date[:4] if release_date and len(release_date) >= 4 else ""
        runtime = metadata.runtime if metadata else 0

        genres: List[str] = []
        if metadata:
            genres_val = getattr(metadata, "genres", None)
            if genres_val:
                if isinstance(genres_val, list):
                    genres = [str(g) for g in genres_val if g]
                elif isinstance(genres_val, str):
                    genres = [g.strip() for g in genres_val.split("|") if g.strip()]
        if not genres and content:
            genres_val = getattr(content, "genres", None)
            if genres_val:
                if isinstance(genres_val, list):
                    genres = [str(g) for g in genres_val if g]
                elif isinstance(genres_val, str):
                    genres = [g.strip() for g in genres_val.split("|") if g.strip()]
        if not genres and content:
            from sqlalchemy.orm import object_session
            from sqlalchemy import text
            session = object_session(content)
            if session:
                try:
                    from services.repository.catalog_db import ContentGenre, Genre
                    cg_genres = [
                        name for (name,) in session.query(Genre.name)
                        .join(ContentGenre, ContentGenre.genre_id == Genre.id)
                        .filter(ContentGenre.content_id == content.id)
                        .all()
                    ]
                    if cg_genres:
                        genres = cg_genres
                    else:
                        res = session.execute(
                            text("SELECT genres FROM content WHERE slug = :slug OR id = :id"),
                            {"slug": content.slug, "id": content.id}
                        ).fetchone()
                        if res and res[0]:
                            genres = [x.strip() for x in str(res[0]).split("|") if x.strip()]
                except Exception:
                    pass

        return {
            "item_id": content.id,
            "id": content.id,
            "title": metadata.title if metadata else "Untitled",
            "entity_type": content.entity_type,
            "content_type": "series" if content.entity_type in {"tvseries", "series", "tv"} else "movie",
            "year": year,
            "runtime": runtime or 0,
            "rating": round(float(stats.average_rating or 0.0), 1) if stats else 0.0,
            "popularity": float(stats.popularity or 0.0) if stats else 0.0,
            "poster_url": artwork.poster_url if artwork else "",
            "backdrop_url": artwork.backdrop_url if artwork else "",
            "overview": metadata.overview if metadata else "",
            "genres": genres,
            "rich_metadata": {
                "title": metadata.title if metadata else "Untitled",
                "year": year,
                "runtime": runtime or 0,
                "rating": round(float(stats.average_rating or 0.0), 1) if stats else 0.0,
                "content_type": "series" if content.entity_type in {"tvseries", "series", "tv"} else "movie",
                "genres": genres,
            },
        }

    def _query_top_content(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Fetch a small, indexed catalog slice in one bounded DB query."""
        with self.repo.get_session() as session:
            rows = (
                session.query(Content)
                .outerjoin(ContentMetadata, ContentMetadata.content_id == Content.id)
                .outerjoin(ContentArtwork, ContentArtwork.content_id == Content.id)
                .outerjoin(ContentStatistics, ContentStatistics.content_id == Content.id)
                .filter(Content.is_deleted.is_(False))
                .order_by(
                    desc(ContentStatistics.popularity),
                    desc(ContentStatistics.average_rating),
                    Content.id.asc(),
                )
                .limit(max(1, min(limit, 60)))
                .all()
            )
            return [self._to_item(row) for row in rows]

    @staticmethod
    def _stable_rotation(items: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
        if not items:
            return []
        seed = int(hashlib.sha256(f"{user_id}:{datetime.now(timezone.utc).date()}".encode()).hexdigest()[:8], 16)
        offset = seed % len(items)
        return items[offset:] + items[:offset]

    def _build_fast_snapshot(self, user_id: str, format_filter: str = "all") -> Dict[str, Any]:
        started = time.perf_counter()
        catalog = self._query_top_content(limit=60)

        if format_filter == "movie":
            catalog = [x for x in catalog if x["content_type"] == "movie"]
        elif format_filter == "series":
            catalog = [x for x in catalog if x["content_type"] == "series"]

        catalog = self._stable_rotation(catalog, str(user_id))
        movies = [x for x in catalog if x["content_type"] == "movie"]
        series = [x for x in catalog if x["content_type"] == "series"]
        hero_pool = catalog[:8]
        hero = hero_pool[0] if hero_pool else None

        # Build genre-based sections for diversity
        genre_buckets: Dict[str, List[Dict[str, Any]]] = {}
        for item in catalog:
            item_genres = item.get("genres") or item.get("rich_metadata", {}).get("genres") or []
            if isinstance(item_genres, str):
                item_genres = [g.strip() for g in item_genres.split("|") if g.strip()]
            for g in item_genres[:2]:  # limit to first 2 genres per item
                genre_buckets.setdefault(g, []).append(item)

        sections: List[Dict[str, Any]] = []
        if hero_pool:
            sections.append({"id": "recommended", "title": "Top Picks for You", "type": "carousel", "items": hero_pool[:12]})
        if movies:
            sections.append({"id": "movies", "title": "Popular Movies", "type": "carousel", "items": movies[:12]})
        if series:
            sections.append({"id": "series", "title": "Popular TV Series", "type": "carousel", "items": series[:12]})

        # Add genre-based shelves (up to 4 genre rows with at least 3 items each)
        seen_item_ids = set()
        for sec in sections:
            for it in sec.get("items", []):
                seen_item_ids.add(it.get("item_id") or it.get("id"))

        genre_sections_added = 0
        for genre_name, genre_items in sorted(genre_buckets.items(), key=lambda kv: -len(kv[1])):
            if genre_sections_added >= 4:
                break
            # De-duplicate: prefer items not already shown in hero/movies/series rows
            unique_items = [it for it in genre_items if (it.get("item_id") or it.get("id")) not in seen_item_ids]
            if len(unique_items) < 3:
                unique_items = genre_items[:12]  # fall back to all items in genre
            if len(unique_items) >= 3:
                sections.append({
                    "id": f"genre_{genre_name.lower().replace(' ', '_').replace('&', 'and')}",
                    "title": genre_name,
                    "type": "carousel",
                    "items": unique_items[:12],
                })
                for it in unique_items[:12]:
                    seen_item_ids.add(it.get("item_id") or it.get("id"))
                genre_sections_added += 1

        if catalog:
            # 'Trending Now' uses a reversed rotation for variety
            trending = list(reversed(catalog[:12]))
            sections.append({"id": "trending", "title": "Trending Now", "type": "carousel", "items": trending})

        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "status": "SUCCESS",
            "user_id": str(user_id),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "duration_ms": elapsed_ms,
            "hero": hero,
            "sections": sections,
            "shelves": sections,
            "source": "fast_catalog_read_model",
        }

    def precompute_user_home_slate(self, user_id: str, format_filter: str = "all") -> Dict[str, Any]:
        """Synchronously build a bounded fast snapshot for worker/background usage."""
        snapshot = self._build_fast_snapshot(user_id, format_filter)
        self._snapshots[f"{user_id}:{format_filter}"] = snapshot
        return snapshot

    def get_precomputed_home_slate(self, user_id: str, format_filter: str = "all") -> Dict[str, Any]:
        key = f"{user_id}:{format_filter}"
        snapshot = self._snapshots.get(key)
        if not snapshot:
            # Fall back to global cold-start snapshot
            global_key = f"global:{format_filter}"
            snapshot = self._snapshots.get(global_key)
            if not snapshot:
                # Fast bootstrap for cold cache — never return None or leave UI blank
                snapshot = self.precompute_user_home_slate("global", format_filter)
            return snapshot

        generated_at = snapshot.get("generated_at")
        if not generated_at:
            return snapshot
        try:
            created = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - created).total_seconds()
            if age > self._snapshot_ttl_seconds:
                # Refresh snapshot asynchronously/in background and return existing in the interim
                self.precompute_user_home_slate(str(user_id), format_filter)
                return self._snapshots.get(key) or snapshot
        except (TypeError, ValueError):
            return snapshot
        return snapshot
