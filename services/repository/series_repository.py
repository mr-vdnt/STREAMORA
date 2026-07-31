from typing import Optional, Dict, Any, List
from services.repository.catalog_db import CatalogRepository, TVSeries, Season, Episode

class SeriesRepository:
    """
    Dedicated SQLAlchemy-backed repository for TVSeries, Season, and Episode entities.
    Strictly isolated from Movie data pipelines.
    """
    def __init__(self, db_url: Optional[str] = None):
        self.catalog_repo = CatalogRepository(db_url=db_url)

    def get_by_id(self, series_id: int) -> Optional[Dict[str, Any]]:
        with self.catalog_repo.get_session() as session:
            series = session.query(TVSeries).filter(TVSeries.id == series_id).first()
            if not series:
                return None
            
            series_dict = {c.key: getattr(series, c.key) for c in series.__mapper__.columns.values()}
            
            # Fetch seasons and episodes hierarchy
            seasons_list = []
            for s in series.seasons:
                s_dict = {c.key: getattr(s, c.key) for c in s.__mapper__.columns.values()}
                s_dict["episodes"] = [{c.key: getattr(e, c.key) for c in e.__mapper__.columns.values()} for e in s.episodes]
                seasons_list.append(s_dict)
                
            series_dict["seasons"] = seasons_list
            return series_dict

    def get_by_tmdb_id(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        with self.catalog_repo.get_session() as session:
            series = session.query(TVSeries).filter(TVSeries.tmdb_id == tmdb_id).first()
            if not series:
                return None
            return {c.key: getattr(series, c.key) for c in series.__mapper__.columns.values()}

    def get_top_series(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self.catalog_repo.get_session() as session:
            series_items = session.query(TVSeries).order_by(TVSeries.popularity.desc()).limit(limit).all()
            return [{c.key: getattr(s, c.key) for c in s.__mapper__.columns.values()} for s in series_items]

    def save_series(self, series_data: dict) -> int:
        return self.catalog_repo.save_tv_series(series_data)
