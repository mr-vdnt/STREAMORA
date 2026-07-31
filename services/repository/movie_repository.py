from typing import Optional, Dict, Any, List
from services.repository.catalog_db import CatalogRepository, Movie

class MovieRepository:
    """
    Dedicated SQLAlchemy-backed repository for Movie entities.
    Strictly isolated from Series data pipelines.
    """
    def __init__(self, db_url: Optional[str] = None):
        self.catalog_repo = CatalogRepository(db_url=db_url)

    def get_by_id(self, movie_id: int) -> Optional[Dict[str, Any]]:
        with self.catalog_repo.get_session() as session:
            movie = session.query(Movie).filter(Movie.id == movie_id).first()
            if not movie:
                return None
            return {c.key: getattr(movie, c.key) for c in movie.__mapper__.columns.values()}

    def get_by_tmdb_id(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        with self.catalog_repo.get_session() as session:
            movie = session.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
            if not movie:
                return None
            return {c.key: getattr(movie, c.key) for c in movie.__mapper__.columns.values()}

    def get_top_movies(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self.catalog_repo.get_session() as session:
            movies = session.query(Movie).order_by(Movie.popularity.desc()).limit(limit).all()
            return [{c.key: getattr(m, c.key) for c in m.__mapper__.columns.values()} for m in movies]

    def get_all(self) -> Dict[int, Dict[str, Any]]:
        with self.catalog_repo.get_session() as session:
            movies = session.query(Movie).all()
            return {m.id: {c.key: getattr(m, c.key) for c in m.__mapper__.columns.values()} for m in movies}

    def save_movie(self, movie_data: dict) -> int:
        return self.catalog_repo.save_movie(movie_data)
