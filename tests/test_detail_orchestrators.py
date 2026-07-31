import pytest
import asyncio
from services.discovery.movie_orchestrator import MovieDetailOrchestrator
from services.discovery.series_orchestrator import SeriesDetailOrchestrator
from services.repository.catalog_db import CatalogRepository, Movie, TVSeries

def test_movie_detail_orchestrator():
    async def _run():
        repo = CatalogRepository()
        with repo.get_session() as session:
            movie = session.query(Movie).first()
            if not movie:
                repo.save_movie({
                    "tmdb_id": 9991,
                    "title": "Test Orchestrator Movie",
                    "overview": "An epic journey",
                    "poster_url": "/poster.jpg",
                    "backdrop_url": "/backdrop.jpg",
                    "genres": "Action|Sci-Fi",
                    "rating": 8.5,
                    "popularity": 95.0
                })
                movie = session.query(Movie).filter(Movie.tmdb_id == 9991).first()
                
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
            series = session.query(TVSeries).first()
            if not series:
                repo.save_tv_series({
                    "tmdb_id": 9992,
                    "title": "Test Orchestrator Series",
                    "overview": "A series journey",
                    "poster_url": "/sposter.jpg",
                    "backdrop_url": "/sbackdrop.jpg",
                    "genres": "Drama|Mystery",
                    "rating": 9.0,
                    "popularity": 92.0
                })
                series = session.query(TVSeries).filter(TVSeries.tmdb_id == 9992).first()
                
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
