from typing import Dict, Any, Optional
from services.catalog.normalizer import MetadataNormalizer
from services.repository.movie_repository import MovieRepository
from services.repository.series_repository import SeriesRepository

class QualityChecker:
    """Validates that normalized metadata meets production quality thresholds."""
    @staticmethod
    def is_valid_movie(item: Dict[str, Any]) -> bool:
        return bool(item.get("title") and item.get("tmdb_id"))

    @staticmethod
    def is_valid_series(item: Dict[str, Any]) -> bool:
        return bool(item.get("title") and item.get("tmdb_id"))


class ContentIngestionService:
    """
    Canonical Content Ingestion Pipeline:
    External Payloads ➔ MetadataNormalizer ➔ QualityChecker ➔ Domain Repository
    """
    def __init__(self):
        self.movie_repo = MovieRepository()
        self.series_repo = SeriesRepository()
        self.normalizer = MetadataNormalizer()
        self.quality_checker = QualityChecker()

    def ingest_movie(self, raw_payload: Dict[str, Any]) -> Optional[int]:
        normalized = self.normalizer.normalize_movie(raw_payload)
        if not self.quality_checker.is_valid_movie(normalized):
            return None
        return self.movie_repo.save_movie(normalized)

    def ingest_series(self, raw_payload: Dict[str, Any]) -> Optional[int]:
        normalized = self.normalizer.normalize_series(raw_payload)
        if not self.quality_checker.is_valid_series(normalized):
            return None
        return self.series_repo.save_series(normalized)
