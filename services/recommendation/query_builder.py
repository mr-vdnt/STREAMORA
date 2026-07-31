from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from services.repository.catalog_db import Content
from services.recommendation.specifications import Specification

class CandidateQueryBuilder:
    """
    Translates Specification objects into SQLAlchemy candidate queries.
    """
    def __init__(self, session: Session, entity_model: Any = Content):
        self.session = session
        self.entity_model = entity_model
        self.query = self.session.query(self.entity_model)

    def with_specification(self, spec: Optional[Specification]) -> 'CandidateQueryBuilder':
        if spec:
            self.query = spec.apply_filter(self.query)
        return self

    def order_by_popularity(self, descending: bool = True) -> 'CandidateQueryBuilder':
        if descending:
            self.query = self.query.order_by(desc(Content.popularity))
        else:
            self.query = self.query.order_by(asc(Content.popularity))
        return self

    def order_by_rating(self, descending: bool = True) -> 'CandidateQueryBuilder':
        if descending:
            self.query = self.query.order_by(desc(Content.rating))
        else:
            self.query = self.query.order_by(asc(Content.rating))
        return self

    def execute(self, limit: int = 100) -> List[Dict[str, Any]]:
        results = self.query.limit(limit).all()
        return [{c.key: getattr(item, c.key) for c in item.__mapper__.columns.values()} for item in results]
