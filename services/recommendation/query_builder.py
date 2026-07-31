from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from services.repository.catalog_db import Content, ContentMetadata, ContentArtwork, ContentStatistics
from services.recommendation.specifications import Specification

class CandidateQueryBuilder:
    """
    Translates Specification objects into SQLAlchemy candidate queries with pre-joined relationships.
    """
    def __init__(self, session: Session, entity_model: Any = Content):
        self.session = session
        self.entity_model = entity_model
        # Join relationships once to prevent duplicate join clauses
        self.query = self.session.query(self.entity_model)\
            .outerjoin(ContentMetadata, Content.id == ContentMetadata.content_id)\
            .outerjoin(ContentStatistics, Content.id == ContentStatistics.content_id)\
            .outerjoin(ContentArtwork, Content.id == ContentArtwork.content_id)\
            .filter(Content.is_deleted == False)

    def with_specification(self, spec: Optional[Specification]) -> 'CandidateQueryBuilder':
        if spec:
            self.query = spec.apply_filter(self.query)
        return self

    def order_by_popularity(self, descending: bool = True) -> 'CandidateQueryBuilder':
        if descending:
            self.query = self.query.order_by(desc(ContentStatistics.popularity))
        else:
            self.query = self.query.order_by(asc(ContentStatistics.popularity))
        return self

    def order_by_rating(self, descending: bool = True) -> 'CandidateQueryBuilder':
        if descending:
            self.query = self.query.order_by(desc(ContentStatistics.average_rating))
        else:
            self.query = self.query.order_by(asc(ContentStatistics.average_rating))
        return self

    def execute(self, limit: int = 100) -> List[Dict[str, Any]]:
        results = self.query.limit(limit).all()
        formatted = []
        for item in results:
            meta = item.metadata_rel
            art = item.artwork_rel
            stats = item.statistics_rel
            formatted.append({
                "id": item.id,
                "uuid": item.uuid,
                "slug": item.slug,
                "entity_type": item.entity_type,
                "title": meta.title if meta else "",
                "overview": meta.overview if meta else "",
                "poster_url": art.poster_url if art else "",
                "backdrop_url": art.backdrop_url if art else "",
                "rating": stats.average_rating if stats else 0.0,
                "popularity": stats.popularity if stats else 0.0,
                "genres": "General"
            })
        return formatted
