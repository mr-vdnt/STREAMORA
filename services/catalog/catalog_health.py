from typing import Dict, Any, List
from services.repository.catalog_db import CatalogRepository, Content

class CatalogHealthService:
    """
    Catalog Intelligence & Quality Health Subsystem.
    Continuously audits catalog metadata completeness, missing assets, and health scores.
    """
    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    def audit_catalog_health(self) -> Dict[str, Any]:
        with self.repo.get_session() as session:
            total_items = session.query(Content).count()
            if total_items == 0:
                return {
                    "health_score": 100.0,
                    "total_items": 0,
                    "issues": []
                }

            missing_posters = session.query(Content).filter((Content.poster_url == None) | (Content.poster_url == "")).count()
            missing_backdrops = session.query(Content).filter((Content.backdrop_url == None) | (Content.backdrop_url == "")).count()
            missing_overviews = session.query(Content).filter((Content.overview == None) | (Content.overview == "")).count()
            missing_ratings = session.query(Content).filter((Content.rating == None) | (Content.rating == 0.0)).count()

            # Calculate quality penalties
            penalty = (missing_posters * 10) + (missing_backdrops * 5) + (missing_overviews * 5) + (missing_ratings * 2)
            health_score = max(0.0, round(100.0 - (penalty / total_items), 1))

            return {
                "health_score": health_score,
                "total_items": total_items,
                "metrics": {
                    "missing_posters": missing_posters,
                    "missing_backdrops": missing_backdrops,
                    "missing_overviews": missing_overviews,
                    "missing_ratings": missing_ratings
                },
                "status": "Healthy" if health_score >= 80.0 else "Degraded"
            }
