from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from services.repository.catalog_db import ExternalIdentifier, Content, ContentMetadata

class DuplicateDetectionService:
    """
    Multi-signal duplicate detection service based on ExternalIdentifiers and title fuzzy matching.
    """
    def __init__(self, session: Session):
        self.session = session

    def find_duplicate_by_external_id(self, provider_name: str, external_id: str) -> Optional[int]:
        ext = self.session.query(ExternalIdentifier).filter(
            ExternalIdentifier.provider_name == provider_name,
            ExternalIdentifier.external_id == str(external_id)
        ).first()
        return ext.content_id if ext else None

    def find_duplicates_by_title_and_year(self, title: str, release_date: str) -> List[int]:
        year = str(release_date)[:4] if release_date else ""
        results = self.session.query(ContentMetadata).filter(
            ContentMetadata.title.ilike(title)
        ).all()

        duplicate_ids = []
        for meta in results:
            meta_year = str(meta.release_date)[:4] if meta.release_date else ""
            if not year or not meta_year or year == meta_year:
                duplicate_ids.append(meta.content_id)
        return duplicate_ids
