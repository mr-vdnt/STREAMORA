import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime

Base = declarative_base()

class MovieModel(Base):
    __tablename__ = 'movies'
    
    item_id = Column(Integer, primary_key=True)
    tmdb_id = Column(Integer, index=True, nullable=True)
    title = Column(String(255), nullable=False)
    original_title = Column(String(255))
    release_date = Column(String(50))
    year = Column(String(10), index=True)
    runtime = Column(String(50))
    genres = Column(String(500))  # Pipe-separated
    overview = Column(Text)
    tagline = Column(String(500))
    director = Column(String(255))
    cast = Column(Text)  # JSON or Pipe-separated string
    poster_url = Column(String(500))
    backdrop_url = Column(String(500))
    rating = Column(Float, default=0.0, index=True)
    popularity = Column(Float, default=0.0, index=True)
    language = Column(String(10))
    content_type = Column(String(50), index=True) # movie, series, anime, documentary
    themes = Column(String(500)) # Pipe-separated
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CatalogRepository:
    """
    SQLAlchemy-backed repository for the movie catalog.
    Can operate on SQLite or PostgreSQL depending on connection string.
    """
    def __init__(self, db_url=None):
        if db_url is None:
            # Default to SQLite in the data folder
            db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/catalog.db'))
            db_url = f"sqlite:///{db_path}"
            
        is_sqlite = db_url.startswith("sqlite")
        
        if is_sqlite:
            # SQLite specific configuration for thread safety
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

    def get_by_id(self, item_id: int):
        with self.get_session() as session:
            movie = session.query(MovieModel).filter(MovieModel.item_id == item_id).first()
            return self._to_dict(movie) if movie else None
            
    def get_by_tmdb_id(self, tmdb_id: int):
        with self.get_session() as session:
            movie = session.query(MovieModel).filter(MovieModel.tmdb_id == tmdb_id).first()
            return self._to_dict(movie) if movie else None

    def get_all(self):
        """Returns all movies mapped by item_id (useful for memory caching)"""
        with self.get_session() as session:
            movies = session.query(MovieModel).all()
            return {m.item_id: self._to_dict(m) for m in movies}
            
    def save(self, movie_data: dict):
        """Inserts or updates a movie record"""
        with self.get_session() as session:
            # Ensure required fields
            item_id = movie_data.get('item_id')
            if not item_id:
                # Generate a new item_id safely
                item_id = movie_data.get('tmdb_id')
                if not item_id:
                    max_id = session.query(MovieModel).order_by(MovieModel.item_id.desc()).first()
                    item_id = (max_id.item_id + 1) if max_id else 1
                movie_data['item_id'] = item_id
                
            existing = session.query(MovieModel).filter(MovieModel.item_id == item_id).first()
            if existing:
                for key, value in movie_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
            else:
                new_movie = MovieModel(**{k: v for k, v in movie_data.items() if hasattr(MovieModel, k)})
                session.add(new_movie)
                
            session.commit()
            return item_id

    def get_genres(self):
        """Returns a list of unique genres from the database."""
        with self.get_session() as session:
            # Note: genres are pipe-separated in the DB.
            # In a real app we'd normalize them, but here we just extract and split.
            movies = session.query(MovieModel.genres).filter(MovieModel.genres != None).all()
            unique_genres = set()
            for (genres_str,) in movies:
                if genres_str:
                    for g in genres_str.split('|'):
                        if g.strip():
                            unique_genres.add(g.strip())
            return sorted(list(unique_genres))

    def _to_dict(self, model_instance):
        if not model_instance:
            return None
        return {c.name: getattr(model_instance, c.name) for c in model_instance.__table__.columns}
