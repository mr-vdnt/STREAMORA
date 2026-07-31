from typing import Optional, Dict, Any, List
from services.repository.catalog_db import (
    CatalogRepository, Content, ContentMetadata, ContentArtwork, ContentStatistics, MovieDetails, ExternalIdentifier
)

class MovieRepository:
    """
    Repository operating on Movie aggregate root.
    Exposes domain operations without direct inter-repository calls.
    """
    def __init__(self, db_url: Optional[str] = None):
        self.catalog_repo = CatalogRepository(db_url=db_url)

    def find_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        with self.catalog_repo.get_session() as session:
            content = session.query(Content).filter(Content.slug == slug, Content.entity_type == 'movie', Content.is_deleted == False).first()
            return self._to_dict(session, content) if content else None

    def find_by_uuid(self, content_uuid: str) -> Optional[Dict[str, Any]]:
        with self.catalog_repo.get_session() as session:
            content = session.query(Content).filter(Content.uuid == content_uuid, Content.is_deleted == False).first()
            return self._to_dict(session, content) if content else None

    def find_by_id(self, content_id: int) -> Optional[Dict[str, Any]]:
        with self.catalog_repo.get_session() as session:
            content = session.query(Content).filter(Content.id == content_id, Content.is_deleted == False).first()
            return self._to_dict(session, content) if content else None

    def find_by_external_id(self, provider_name: str, external_id: str) -> Optional[Dict[str, Any]]:
        with self.catalog_repo.get_session() as session:
            ext = session.query(ExternalIdentifier).filter(
                ExternalIdentifier.provider_name == provider_name,
                ExternalIdentifier.external_id == str(external_id)
            ).first()
            if not ext:
                return None
            return self.find_by_id(ext.content_id)

    def get_top_movies(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self.catalog_repo.get_session() as session:
            results = session.query(Content).join(ContentStatistics).filter(
                Content.entity_type == 'movie', Content.is_deleted == False
            ).order_by(ContentStatistics.popularity.desc()).limit(limit).all()
            return [self._to_dict(session, c) for c in results]

    def get_all(self) -> Dict[int, Dict[str, Any]]:
        with self.catalog_repo.get_session() as session:
            movies = session.query(Content).filter(Content.entity_type == 'movie', Content.is_deleted == False).all()
            return {m.id: self._to_dict(session, m) for m in movies}

    def get_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        return self.find_by_id(item_id)

    def _to_dict(self, session, content: Content) -> Dict[str, Any]:
        meta = content.metadata_rel
        art = content.artwork_rel
        stats = content.statistics_rel
        details = content.movie_details_rel

        return {
            "id": content.id,
            "uuid": content.uuid,
            "slug": content.slug,
            "entity_type": content.entity_type,
            "title": meta.title if meta else "",
            "original_title": meta.original_title if meta else "",
            "overview": meta.overview if meta else "",
            "tagline": meta.tagline if meta else "",
            "release_date": meta.release_date if meta else "",
            "runtime": meta.runtime if meta else 0,
            "language": meta.language if meta else "en",
            "poster_url": art.poster_url if art else "",
            "backdrop_url": art.backdrop_url if art else "",
            "popularity": stats.popularity if stats else 0.0,
            "rating": stats.average_rating if stats else 0.0,
            "budget": details.budget if details else "",
            "revenue": details.revenue if details else "",
            "mpaa_rating": details.mpaa_rating if details else ""
        }
