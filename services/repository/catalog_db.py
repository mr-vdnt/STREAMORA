import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.pool import StaticPool
from datetime import datetime

Base = declarative_base()

class Content(Base):
    __tablename__ = 'content'
    
    # Immutable Identity
    id = Column(Integer, primary_key=True, autoincrement=True)
    tmdb_id = Column(Integer, index=True, nullable=True)
    imdb_id = Column(String(50), nullable=True)
    slug = Column(String(255), unique=True, index=True)
    entity_type = Column(String(50), nullable=False) # 'movie' or 'tvseries'
    
    # Common Metadata
    title = Column(String(255), nullable=False)
    original_title = Column(String(255))
    release_date = Column(String(50))
    year = Column(String(10), index=True)
    genres = Column(String(500))  # Pipe-separated
    themes = Column(String(500))  # Pipe-separated
    overview = Column(Text)
    poster_url = Column(String(500))
    backdrop_url = Column(String(500))
    rating = Column(Float, default=0.0, index=True)
    popularity = Column(Float, default=0.0, index=True)
    language = Column(String(10))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __mapper_args__ = {
        'polymorphic_on': entity_type,
        'polymorphic_identity': 'content'
    }

class Movie(Content):
    __tablename__ = 'movies'
    id = Column(Integer, ForeignKey('content.id'), primary_key=True)
    runtime = Column(Integer)  # in minutes
    tagline = Column(String(500))
    director = Column(String(255))
    cast = Column(Text)  # Pipe-separated or JSON
    
    __mapper_args__ = {
        'polymorphic_identity': 'movie',
    }

class TVSeries(Content):
    __tablename__ = 'tv_series'
    id = Column(Integer, ForeignKey('content.id'), primary_key=True)
    total_seasons = Column(Integer, default=0)
    total_episodes = Column(Integer, default=0)
    in_production = Column(Boolean, default=False)
    creator = Column(String(255))
    cast = Column(Text)
    
    seasons = relationship("Season", back_populates="series", cascade="all, delete-orphan")

    __mapper_args__ = {
        'polymorphic_identity': 'tvseries',
    }

class Season(Base):
    __tablename__ = 'seasons'
    id = Column(Integer, primary_key=True, autoincrement=True)
    series_id = Column(Integer, ForeignKey('tv_series.id'))
    season_number = Column(Integer, nullable=False)
    title = Column(String(255))
    overview = Column(Text)
    poster_url = Column(String(500))
    release_date = Column(String(50))
    
    series = relationship("TVSeries", back_populates="seasons")
    episodes = relationship("Episode", back_populates="season", cascade="all, delete-orphan")

class Episode(Base):
    __tablename__ = 'episodes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    season_id = Column(Integer, ForeignKey('seasons.id'))
    episode_number = Column(Integer, nullable=False)
    title = Column(String(255))
    overview = Column(Text)
    still_url = Column(String(500))
    runtime = Column(Integer)
    rating = Column(Float, default=0.0)
    release_date = Column(String(50))
    
    season = relationship("Season", back_populates="episodes")


class CatalogRepository:
    """
    SQLAlchemy-backed repository for the new normalized catalog.
    """
    def __init__(self, db_url=None):
        if db_url is None:
            db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/catalog_v2.db'))
            db_url = f"sqlite:///{db_path}"
            
        is_sqlite = db_url.startswith("sqlite")
        
        if is_sqlite:
            self.engine = create_engine(
                db_url, 
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
        else:
            self.engine = create_engine(db_url)
            
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def get_session(self):
        return self.SessionLocal()

    def get_by_id(self, content_id: int):
        with self.get_session() as session:
            content = session.query(Content).filter(Content.id == content_id).first()
            return self._to_dict(content) if content else None

    def get_by_tmdb_id(self, tmdb_id: int, entity_type: str = None):
        with self.get_session() as session:
            query = session.query(Content).filter(Content.tmdb_id == tmdb_id)
            if entity_type:
                query = query.filter(Content.entity_type == entity_type)
            content = query.first()
            return self._to_dict(content) if content else None

    def get_by_slug(self, slug: str):
        with self.get_session() as session:
            content = session.query(Content).filter(Content.slug == slug).first()
            return self._to_dict(content) if content else None

    def save_movie(self, movie_data: dict):
        with self.get_session() as session:
            movie = Movie(**{k: v for k, v in movie_data.items() if hasattr(Movie, k)})
            session.add(movie)
            session.commit()
            return movie.id

    def save_tv_series(self, series_data: dict):
        with self.get_session() as session:
            series = TVSeries(**{k: v for k, v in series_data.items() if hasattr(TVSeries, k)})
            session.add(series)
            session.commit()
            return series.id

    def _to_dict(self, model_instance):
        if not model_instance:
            return None
        return {c.key: getattr(model_instance, c.key) for c in model_instance.__mapper__.columns.values()}
