from abc import ABC, abstractmethod
from typing import Any, List, Optional
from sqlalchemy import or_, and_, desc
from services.repository.catalog_db import Content, ContentMetadata, ContentStatistics

class Specification(ABC):
    """Abstract base class for all specifications."""
    
    @abstractmethod
    def apply_filter(self, query: Any) -> Any:
        """Apply SQLAlchemy filter criteria to a query."""
        pass
        
    def __and__(self, other: 'Specification') -> 'Specification':
        return AndSpecification(self, other)

    def __or__(self, other: 'Specification') -> 'Specification':
        return OrSpecification(self, other)

    def __invert__(self) -> 'Specification':
        return NotSpecification(self)


class MovieOnlySpecification(Specification):
    def apply_filter(self, query: Any) -> Any:
        return query.filter(Content.entity_type == 'movie')


class SeriesOnlySpecification(Specification):
    def apply_filter(self, query: Any) -> Any:
        return query.filter(Content.entity_type == 'tvseries')


class TrendingIndiaSpecification(Specification):
    def __init__(self, min_popularity: float = 40.0):
        self.min_popularity = min_popularity

    def apply_filter(self, query: Any) -> Any:
        return query.filter(
            and_(
                Content.language.in_(['hi', 'te', 'ta', 'kn', 'ml', 'mr', 'bn', 'in', 'en']),
                Content.popularity >= self.min_popularity
            )
        )


class GenreSpecification(Specification):
    def __init__(self, genre: str):
        self.genre = genre

    def apply_filter(self, query: Any) -> Any:
        return query.filter(Content.genres.ilike(f"%{self.genre}%"))


class ThemeSpecification(Specification):
    def __init__(self, theme: str):
        self.theme = theme

    def apply_filter(self, query: Any) -> Any:
        return query.filter(Content.themes.ilike(f"%{self.theme}%"))


class MinRatingSpecification(Specification):
    def __init__(self, min_rating: float):
        self.min_rating = min_rating

    def apply_filter(self, query: Any) -> Any:
        return query.filter(Content.rating >= self.min_rating)


class MinPopularitySpecification(Specification):
    def __init__(self, min_popularity: float):
        self.min_popularity = min_popularity

    def apply_filter(self, query: Any) -> Any:
        return query.filter(Content.popularity >= self.min_popularity)


class LanguageSpecification(Specification):
    def __init__(self, languages: List[str]):
        self.languages = languages

    def apply_filter(self, query: Any) -> Any:
        return query.filter(Content.language.in_(self.languages))


class ExcludeIDsSpecification(Specification):
    def __init__(self, exclude_ids: set):
        self.exclude_ids = exclude_ids

    def apply_filter(self, query: Any) -> Any:
        if not self.exclude_ids:
            return query
        return query.filter(~Content.id.in_(list(self.exclude_ids)))


class AndSpecification(Specification):
    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right

    def apply_filter(self, query: Any) -> Any:
        query = self.left.apply_filter(query)
        return self.right.apply_filter(query)


class OrSpecification(Specification):
    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right

    def apply_filter(self, query: Any) -> Any:
        return self.left.apply_filter(query)


class NotSpecification(Specification):
    def __init__(self, spec: Specification):
        self.spec = spec

    def apply_filter(self, query: Any) -> Any:
        return query
