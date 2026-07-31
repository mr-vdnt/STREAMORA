from typing import Optional, Dict, Any, List
from services.repository.catalog_db import (
    CatalogRepository, Content, ContentMetadata, ContentArtwork, ContentStatistics, SeriesDetails, Season, Episode, ExternalIdentifier
)

class SeriesRepository:
    """
    Repository operating on Series aggregate root (Series, Season, Episode).
    Exposes domain operations without direct inter-repository calls.
    """
    def __init__(self, db_url: Optional[str] = None):
        self.catalog_repo = CatalogRepository(db_url=db_url)

    def find_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        with self.catalog_repo.get_session() as session:
            content = session.query(Content).filter(Content.slug == slug, Content.entity_type == 'tvseries', Content.is_deleted == False).first()
            return self._to_dict(session, content) if content else None

    def find_by_uuid(self, content_uuid: str) -> Optional[Dict[str, Any]]:
        with self.catalog_repo.get_session() as session:
            content = session.query(Content).filter(Content.uuid == content_uuid, Content.is_deleted == False).first()
            return self._to_dict(session, content) if content else None

    def find_by_id(self, content_id: int) -> Optional[Dict[str, Any]]:
        with self.catalog_repo.get_session() as session:
            content = session.query(Content).filter(Content.id == content_id, Content.is_deleted == False).first()
            return self._to_dict(session, content) if content else None

    def get_top_series(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self.catalog_repo.get_session() as session:
            results = session.query(Content).join(ContentStatistics).filter(
                Content.entity_type == 'tvseries', Content.is_deleted == False
            ).order_by(ContentStatistics.popularity.desc()).limit(limit).all()
            return [self._to_dict(session, c) for c in results]

    def get_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        return self.find_by_id(item_id)

    def _to_dict(self, session, content: Content) -> Dict[str, Any]:
        meta = content.metadata_rel
        art = content.artwork_rel
        stats = content.statistics_rel
        details = content.series_details_rel

        # Fetch seasons and episodes
        seasons = session.query(Season).filter(Season.series_content_id == content.id, Season.is_deleted == False).all()
        seasons_list = []
        for s in seasons:
            episodes = session.query(Episode).filter(Episode.season_id == s.id, Episode.is_deleted == False).all()
            seasons_list.append({
                "id": s.id,
                "uuid": s.uuid,
                "season_number": s.season_number,
                "title": s.title,
                "overview": s.overview,
                "episodes": [{
                    "id": ep.id,
                    "uuid": ep.uuid,
                    "episode_number": ep.episode_number,
                    "title": ep.title,
                    "overview": ep.overview,
                    "runtime": ep.runtime,
                    "rating": ep.rating
                } for ep in episodes]
            })

        return {
            "id": content.id,
            "uuid": content.uuid,
            "slug": content.slug,
            "entity_type": content.entity_type,
            "title": meta.title if meta else "",
            "original_title": meta.original_title if meta else "",
            "overview": meta.overview if meta else "",
            "poster_url": art.poster_url if art else "",
            "backdrop_url": art.backdrop_url if art else "",
            "popularity": stats.popularity if stats else 0.0,
            "rating": stats.average_rating if stats else 0.0,
            "total_seasons": details.total_seasons if details else 1,
            "total_episodes": details.total_episodes if details else 1,
            "seasons": seasons_list
        }
