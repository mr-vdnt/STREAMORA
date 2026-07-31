import re
import unicodedata
from sqlalchemy.orm import Session
from services.repository.catalog_db import SearchDocument, ContentMetadata

class SearchPreparationService:
    """
    Pre-populates SearchDocument table with ASCII, normalized, and phonetic tokens.
    """
    @staticmethod
    def _to_ascii(text: str) -> str:
        normalized = unicodedata.normalize('NFKD', text or "").encode('ascii', 'ignore').decode('utf-8')
        return re.sub(r'[^a-zA-Z0-9\s]', '', normalized).lower()

    @staticmethod
    def _to_phonetic(text: str) -> str:
        # Simple phonetic transformation rule
        ascii_text = SearchPreparationService._to_ascii(text)
        return re.sub(r'[aeiou]', '', ascii_text)

    def prepare_search_document(self, session: Session, content_id: int) -> SearchDocument:
        meta = session.query(ContentMetadata).filter(ContentMetadata.content_id == content_id).first()
        title = meta.title if meta else ""
        
        doc = session.query(SearchDocument).filter(SearchDocument.content_id == content_id).first()
        if not doc:
            doc = SearchDocument(content_id=content_id)
            session.add(doc)

        doc.normalized_title = title.lower()
        doc.ascii_title = self._to_ascii(title)
        doc.phonetic_title = self._to_phonetic(title)
        doc.search_version = 1
        
        session.commit()
        return doc
