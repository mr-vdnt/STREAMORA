import pytest
import asyncio
from services.discovery.movie_orchestrator import MovieDetailOrchestrator
from services.discovery.series_orchestrator import SeriesDetailOrchestrator
from services.repository.catalog_db import CatalogRepository, Content

def test_movie_detail_orchestrator():
    async def _run():
        repo = CatalogRepository()
        with repo.get_session() as session:
            movie = session.query(Content).filter(Content.entity_type == "movie").first()
            if not movie:
                session.close()
                return

            orchestrator = MovieDetailOrchestrator()
            result = await orchestrator.get_movie_detail(movie.id)
            
            assert result is not None
            assert "movie" in result
            assert "media" in result
            assert "credits" in result
            assert "ratings" in result
            assert "providers" in result
            assert "trailers" in result
            assert "reviews" in result
            assert "recommendations" in result
            assert "ai" in result
            
    asyncio.run(_run())

def test_series_detail_orchestrator():
    async def _run():
        repo = CatalogRepository()
        with repo.get_session() as session:
            series = session.query(Content).filter(Content.entity_type == "tvseries").first()
            if not series:
                session.close()
                return

            orchestrator = SeriesDetailOrchestrator()
            result = await orchestrator.get_series_detail(series.id)
            
            assert result is not None
            assert "series" in result
            assert "media" in result
            assert "seasons" in result
            assert "episodes" in result
            assert "ratings" in result
            assert "recommendations" in result
            assert "ai" in result
            
    asyncio.run(_run())
