import os
import uuid
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, CheckConstraint, UniqueConstraint, inspect, text
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.pool import StaticPool

Base = declarative_base()

class Content(Base):
    __tablename__ = 'contents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid.uuid4()))
    slug = Column(String(255), unique=True, nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True) # 'movie', 'tvseries', etc.
    status = Column(String(50), default="released")
    
    # Optimistic Concurrency & Versioning
    version_number = Column(Integer, default=1, nullable=False)
    etag = Column(String(64), nullable=True)
    
    # Soft Deletes
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    metadata_rel = relationship("ContentMetadata", uselist=False, back_populates="content", cascade="all, delete-orphan")
    artwork_rel = relationship("ContentArtwork", uselist=False, back_populates="content", cascade="all, delete-orphan")
    statistics_rel = relationship("ContentStatistics", uselist=False, back_populates="content", cascade="all, delete-orphan")
    movie_details_rel = relationship("MovieDetails", uselist=False, back_populates="content", cascade="all, delete-orphan")
    series_details_rel = relationship("SeriesDetails", uselist=False, back_populates="content", cascade="all, delete-orphan")
    external_ids = relationship("ExternalIdentifier", back_populates="content", cascade="all, delete-orphan")
    aliases = relationship("ContentAlias", back_populates="content", cascade="all, delete-orphan")

    def to_graph_node(self) -> dict:
        return {
            "node_uuid": self.uuid,
            "node_type": self.entity_type,
            "slug": self.slug,
            "title": self.metadata_rel.title if self.metadata_rel else ""
        }


class ContentMetadata(Base):
    __tablename__ = 'content_metadata'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey('contents.id'), unique=True, nullable=False)
    title = Column(String(255), nullable=False, index=True)
    original_title = Column(String(255))
    overview = Column(Text)
    tagline = Column(String(500))
    release_date = Column(String(50))
    runtime = Column(Integer, default=0)
    language = Column(String(10), default="en")

    content = relationship("Content", back_populates="metadata_rel")


class ContentArtwork(Base):
    __tablename__ = 'content_artwork'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey('contents.id'), unique=True, nullable=False)
    poster_url = Column(String(500))
    backdrop_url = Column(String(500))
    logo_url = Column(String(500))
    thumbnail_url = Column(String(500))

    content = relationship("Content", back_populates="artwork_rel")


class ContentStatistics(Base):
    __tablename__ = 'content_statistics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey('contents.id'), unique=True, nullable=False)
    popularity = Column(Float, default=0.0, index=True)
    vote_count = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0, index=True)
    trending_score = Column(Float, default=0.0)

    content = relationship("Content", back_populates="statistics_rel")

    __table_args__ = (
        CheckConstraint('average_rating >= 0.0 AND average_rating <= 10.0', name='check_rating_range'),
    )


class MovieDetails(Base):
    __tablename__ = 'movie_details'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey('contents.id'), unique=True, nullable=False)
    budget = Column(String(50))
    revenue = Column(String(50))
    mpaa_rating = Column(String(20))

    content = relationship("Content", back_populates="movie_details_rel")


class SeriesDetails(Base):
    __tablename__ = 'series_details'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey('contents.id'), unique=True, nullable=False)
    first_air_date = Column(String(50))
    last_air_date = Column(String(50))
    total_seasons = Column(Integer, default=1)
    total_episodes = Column(Integer, default=1)
    in_production = Column(Boolean, default=False)
    status = Column(String(50), default="Ended")

    content = relationship("Content", back_populates="series_details_rel")


class Season(Base):
    __tablename__ = 'seasons'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    series_content_id = Column(Integer, ForeignKey('contents.id'), nullable=False)
    season_number = Column(Integer, nullable=False)
    title = Column(String(255))
    overview = Column(Text)
    poster_url = Column(String(500))
    air_date = Column(String(50))
    episode_count = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)

    episodes = relationship("Episode", back_populates="season", cascade="all, delete-orphan")


class Episode(Base):
    __tablename__ = 'episodes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    season_id = Column(Integer, ForeignKey('seasons.id'), nullable=False)
    episode_number = Column(Integer, nullable=False)
    title = Column(String(255))
    overview = Column(Text)
    still_url = Column(String(500))
    runtime = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    air_date = Column(String(50))
    story_summary = Column(Text)
    is_deleted = Column(Boolean, default=False)

    season = relationship("Season", back_populates="episodes")


class Country(Base):
    __tablename__ = 'countries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, nullable=False) # ISO alpha-2
    name = Column(String(100), nullable=False)


class Person(Base):
    __tablename__ = 'persons'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    biography = Column(Text)
    profile_url = Column(String(500))
    is_deleted = Column(Boolean, default=False)


class Genre(Base):
    __tablename__ = 'genres'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False)
    parent_id = Column(Integer, ForeignKey('genres.id'), nullable=True)


class Collection(Base):
    __tablename__ = 'collections'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    overview = Column(Text)
    poster_url = Column(String(500))
    backdrop_url = Column(String(500))


class Studio(Base):
    __tablename__ = 'studios'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    logo_url = Column(String(500))
    country_id = Column(Integer, ForeignKey('countries.id'), nullable=True)


class Provider(Base):
    __tablename__ = 'providers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    logo_url = Column(String(500))


class ProviderAvailability(Base):
    __tablename__ = 'provider_availabilities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(Integer, ForeignKey('providers.id'), nullable=False)
    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False)
    country_id = Column(Integer, ForeignKey('countries.id'), nullable=True)
    access_type = Column(String(50), default="flatrate") # flatrate, rent, buy
    price = Column(String(20))
    quality = Column(String(20), default="HD") # 4K, 1080p, HD
    hdr_support = Column(Boolean, default=False)
    audio_languages = Column(String(255))
    subtitle_languages = Column(String(255))


# Generic Associations
class ContentPerson(Base):
    __tablename__ = 'content_persons'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False)
    person_id = Column(Integer, ForeignKey('persons.id'), nullable=False)
    role = Column(String(50), nullable=False) # actor, director, writer, producer
    character_name = Column(String(255))
    display_order = Column(Integer, default=0)


class ContentGenre(Base):
    __tablename__ = 'content_genres'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False)
    genre_id = Column(Integer, ForeignKey('genres.id'), nullable=False)


class ContentProvider(Base):
    __tablename__ = 'content_providers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False)
    provider_id = Column(Integer, ForeignKey('providers.id'), nullable=False)


class ContentCollection(Base):
    __tablename__ = 'content_collections'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False)
    collection_id = Column(Integer, ForeignKey('collections.id'), nullable=False)


class ContentStudio(Base):
    __tablename__ = 'content_studios'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False)
    studio_id = Column(Integer, ForeignKey('studios.id'), nullable=False)


class ContentRelationship(Base):
    __tablename__ = 'content_relationships'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_content_id = Column(Integer, ForeignKey('contents.id'), nullable=False)
    target_content_id = Column(Integer, ForeignKey('contents.id'), nullable=False)
    relationship_type = Column(String(100), nullable=False) # Sequel, Prequel, Spin-off, Remake, Same Universe, Inspired By
    weight = Column(Float, default=1.0)
    confidence = Column(Float, default=1.0)
    notes = Column(Text)


class ExternalIdentifier(Base):
    __tablename__ = 'external_identifiers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False)
    provider_name = Column(String(50), nullable=False) # tmdb, imdb, trakt, tvmaze, watchmode
    external_id = Column(String(100), nullable=False)
    last_sync = Column(DateTime, default=datetime.utcnow)
    confidence_score = Column(Float, default=1.0)
    source = Column(String(100), default="ingestion_pipeline")

    content = relationship("Content", back_populates="external_ids")

    __table_args__ = (
        UniqueConstraint('provider_name', 'external_id', name='uq_provider_external_id'),
    )


class ContentAlias(Base):
    __tablename__ = 'content_aliases'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False)
    title = Column(String(255), nullable=False, index=True)
    language = Column(String(10), default="en")
    region = Column(String(10))
    alias_type = Column(String(50), default="alternate")
    priority = Column(Integer, default=1)

    content = relationship("Content", back_populates="aliases")


class HistoryEntry(Base):
    __tablename__ = 'history_entries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False)
    version_number = Column(Integer, nullable=False)
    field_name = Column(String(100), nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    source = Column(String(100))
    actor = Column(String(100), default="system")
    timestamp = Column(DateTime, default=datetime.utcnow)


class OutboxEvent(Base):
    __tablename__ = 'outbox_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    aggregate_type = Column(String(50), nullable=False)
    aggregate_id = Column(String(50), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(Text, nullable=False) # JSON serialized payload
    processed = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SearchDocument(Base):
    __tablename__ = 'search_documents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey('contents.id'), unique=True, nullable=False)
    normalized_title = Column(String(255), nullable=False, index=True)
    ascii_title = Column(String(255), index=True)
    phonetic_title = Column(String(255), index=True)
    aliases = Column(Text)
    keywords = Column(Text)
    search_version = Column(Integer, default=1)


class RecommendationFeatures(Base):
    __tablename__ = 'recommendation_features'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey('contents.id'), unique=True, nullable=False)
    genre_vector = Column(Text)
    theme_vector = Column(Text)
    language_vector = Column(Text)
    provider_vector = Column(Text)
    embedding_provider = Column(String(100), default="sentence-transformers")
    embedding_model = Column(String(100), default="all-MiniLM-L6-v2")
    embedding_dimension = Column(Integer, default=384)
    embedding_version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class CatalogRepository:
    """
    Master SQLAlchemy Catalog Repository backing canonical schema.
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
        self._ensure_schema_up_to_date()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def _ensure_schema_up_to_date(self):
        with self.engine.connect() as conn:
            try:
                # Check if seasons table has uuid column
                seasons_cols = [c["name"] for c in inspect(self.engine).get_columns("seasons")]
                if "uuid" not in seasons_cols:
                    conn.execute(text("ALTER TABLE seasons ADD COLUMN uuid VARCHAR(36)"))
                # Check if episodes table has uuid column
                episodes_cols = [c["name"] for c in inspect(self.engine).get_columns("episodes")]
                if "uuid" not in episodes_cols:
                    conn.execute(text("ALTER TABLE episodes ADD COLUMN uuid VARCHAR(36)"))
                conn.commit()
            except Exception:
                pass
        
    def get_session(self):
        return self.SessionLocal()

    def get_by_id(self, content_id: int):
        with self.get_session() as session:
            c = session.query(Content).filter(Content.id == content_id, Content.is_deleted == False).first()
            if not c:
                return None
            meta = c.metadata_rel
            art = c.artwork_rel
            stats = c.statistics_rel
            return {
                "id": c.id,
                "uuid": c.uuid,
                "slug": c.slug,
                "entity_type": c.entity_type,
                "title": meta.title if meta else "",
                "original_title": meta.original_title if meta else "",
                "overview": meta.overview if meta else "",
                "poster_url": art.poster_url if art else "",
                "backdrop_url": art.backdrop_url if art else "",
                "rating": stats.average_rating if stats else 0.0,
                "popularity": stats.popularity if stats else 0.0,
                "genres": []
            }

    def get_by_slug(self, slug: str):
        with self.get_session() as session:
            c = session.query(Content).filter(Content.slug == slug, Content.is_deleted == False).first()
            if not c:
                return None
            return self.get_by_id(c.id)
