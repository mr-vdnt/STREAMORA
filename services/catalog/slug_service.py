import re
import unicodedata
from typing import Optional
from sqlalchemy.orm import Session
from services.repository.catalog_db import Content

class SlugService:
    """
    Generates deterministic stable human-readable slugs for Content entities.
    """
    @staticmethod
    def generate_slug(title: str, year: Optional[str] = None) -> str:
        # Normalize unicode characters
        normalized = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('utf-8')
        cleaned = re.sub(r'[^a-zA-Z0-9\s-]', '', normalized).strip().lower()
        slug_base = re.sub(r'[\s-]+', '-', cleaned)

        if year:
            year_str = str(year).strip()
            if year_str and not slug_base.endswith(year_str):
                slug_base = f"{slug_base}-{year_str}"

        return slug_base or "untitled"

    @classmethod
    def generate_unique_slug(cls, session: Session, title: str, year: Optional[str] = None) -> str:
        base_slug = cls.generate_slug(title, year)
        candidate = base_slug
        counter = 1

        while session.query(Content).filter(Content.slug == candidate).first() is not None:
            candidate = f"{base_slug}-{counter}"
            counter += 1

        return candidate
