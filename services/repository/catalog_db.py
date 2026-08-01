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


# ─────────────────────────────────────────────────────────────
# Data Acquisition Platform (DAP) — Ingestion Tables
# These tables are isolated from catalog domain models.
# ─────────────────────────────────────────────────────────────

class IngestionJob(Base):
    """Tracks each connector execution run."""
    __tablename__ = 'ingestion_jobs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid.uuid4()))
    connector_name = Column(String(100), nullable=False, index=True)
    job_type = Column(String(50), nullable=False)  # full_sync, incremental, on_demand
    status = Column(String(50), default="pending", index=True)  # pending, running, completed, failed, partial
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    items_fetched = Column(Integer, default=0)
    items_ingested = Column(Integer, default=0)
    items_skipped = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    error_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RawPayload(Base):
    """Immutable record of every provider response."""
    __tablename__ = 'raw_payloads'

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey('ingestion_jobs.id'), nullable=False)
    connector_name = Column(String(100), nullable=False, index=True)
    external_id = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # movie, tvseries
    payload_json = Column(Text, nullable=False)  # Raw JSON from provider
    payload_hash = Column(String(64), nullable=False, index=True)  # SHA-256 for change detection
    fetched_at = Column(DateTime, default=datetime.utcnow)


class SyncCheckpoint(Base):
    """Tracks connector cursor state for incremental sync."""
    __tablename__ = 'sync_checkpoints'

    id = Column(Integer, primary_key=True, autoincrement=True)
    connector_name = Column(String(100), unique=True, nullable=False)
    last_sync_at = Column(DateTime, nullable=False)
    cursor_value = Column(String(255), nullable=True)  # Provider-specific cursor
    items_synced = Column(Integer, default=0)


class DeadLetterRecord(Base):
    """Failed payloads for manual inspection and retry."""
    __tablename__ = 'dead_letter_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey('ingestion_jobs.id'), nullable=False)
    connector_name = Column(String(100), nullable=False, index=True)
    external_id = Column(String(100), nullable=False)
    payload_json = Column(Text, nullable=True)
    failure_stage = Column(String(100), nullable=False)  # validation, normalization, resolution, write
    failure_reason = Column(Text, nullable=False)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    is_resolved = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class IngestionProvenance(Base):
    """Links catalog Content entities back to their ingestion source."""
    __tablename__ = 'ingestion_provenance'

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False)
    connector_name = Column(String(100), nullable=False)
    raw_payload_id = Column(Integer, ForeignKey('raw_payloads.id'), nullable=True)
    job_id = Column(Integer, ForeignKey('ingestion_jobs.id'), nullable=True)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    quality_score = Column(Float, default=0.0)


# ─────────────────────────────────────────────────────────────
# Knowledge & Intelligence Platform (KIP) Models
# ─────────────────────────────────────────────────────────────

class KnowledgeFact(Base):
    """Atomic normalized facts with confidence, source weight, and lifecycle states."""
    __tablename__ = 'knowledge_facts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid.uuid4()))
    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # theme, mood, setting, topic, trope, character, object, narrative, audience_safety
    predicate = Column(String(100), nullable=False, index=True)  # has_theme, has_mood, located_in, features_object
    value = Column(Text, nullable=False)  # "mind-bending", "dream-heist", "totem"
    confidence = Column(Float, default=1.0)  # 0.0 to 1.0
    source_weight = Column(Float, default=0.80)  # Provider / model reliability weight
    state = Column(String(20), default="ACTIVE", index=True)  # ACTIVE, SUPERSEDED, RETRACTED, EXPIRED
    superseded_by_id = Column(Integer, ForeignKey('knowledge_facts.id'), nullable=True)
    retracted_reason = Column(Text, nullable=True)
    source_provider = Column(String(100), nullable=False, default="streamora_kip")
    inference_model = Column(String(100), nullable=False, default="baseline_extractor")
    model_version = Column(String(50), nullable=False, default="1.0.0")
    created_at = Column(DateTime, default=datetime.utcnow)


class KnowledgeAssertion(Base):
    """Structured assertions linking entities and concepts."""
    __tablename__ = 'knowledge_assertions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False, index=True)
    assertion_type = Column(String(50), nullable=False)  # character_role, conflict_structure, thematic_premise
    subject = Column(String(255), nullable=False)
    relationship = Column(String(100), nullable=False)
    target = Column(String(255), nullable=False)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class KnowledgeRelationship(Base):
    """Semantic inter-content relationships (sequels, spin-offs, thematic twins)."""
    __tablename__ = 'knowledge_relationships'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_content_id = Column(Integer, ForeignKey('contents.id'), nullable=False, index=True)
    target_content_id = Column(Integer, ForeignKey('contents.id'), nullable=False, index=True)
    relationship_type = Column(String(50), nullable=False, index=True)  # sequel, prequel, spin_off, shared_universe, thematic_twin
    strength = Column(Float, default=1.0)  # 0.0 to 1.0
    provenance = Column(String(255), default="franchise_engine")
    created_at = Column(DateTime, default=datetime.utcnow)


class InferenceRun(Base):
    """Audit log and execution metrics for intelligence engine runs."""
    __tablename__ = 'inference_runs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False, index=True)
    engine_name = Column(String(100), nullable=False, index=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    prompt_hash = Column(String(64), nullable=True)
    execution_time_ms = Column(Float, default=0.0)
    facts_produced = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class KnowledgeSnapshot(Base):
    """Immutable freeze of atomic facts used for reproducible intelligence materialization."""
    __tablename__ = 'knowledge_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid.uuid4()))
    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False, index=True)
    fact_count = Column(Integer, default=0)
    knowledge_hash = Column(String(64), nullable=False, index=True)  # SHA-256 of active facts
    created_at = Column(DateTime, default=datetime.utcnow)


class IntelligenceProfile(Base):
    """CQRS Materialized Read Model for high-speed API & service consumption."""
    __tablename__ = 'intelligence_profiles'

    content_id = Column(Integer, ForeignKey('contents.id'), primary_key=True)
    snapshot_id = Column(Integer, ForeignKey('knowledge_snapshots.id'), nullable=True)
    profile_version = Column(String(50), default="1.0.0")
    dominant_themes_json = Column(Text, nullable=True)  # JSON List[str]
    dominant_moods_json = Column(Text, nullable=True)  # JSON List[str]
    pacing = Column(String(50), default="steady")  # fast-paced, slow-burn, steady
    narrative_structure = Column(String(100), default="linear")
    audience_rating = Column(String(20), default="PG-13")
    content_warnings_json = Column(Text, nullable=True)  # JSON List[str]
    summary_short = Column(Text, nullable=True)
    summary_medium = Column(Text, nullable=True)
    summary_deep = Column(Text, nullable=True)
    summary_spoiler_free = Column(Text, nullable=True)
    overall_confidence = Column(Float, default=1.0)
    fact_count = Column(Integer, default=0)
    generated_at = Column(DateTime, default=datetime.utcnow)


class FranchiseUniverse(Base):
    """Franchise / Universe aggregate root."""
    __tablename__ = 'franchise_universes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    backdrop_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class FranchiseMember(Base):
    """Links Content to Franchise Universe with chronological and release ordering."""
    __tablename__ = 'franchise_members'

    id = Column(Integer, primary_key=True, autoincrement=True)
    franchise_id = Column(Integer, ForeignKey('franchise_universes.id'), nullable=False, index=True)
    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False, index=True)
    chronological_order = Column(Integer, default=1)
    release_order = Column(Integer, default=1)
    timeline_era = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────────────────────
# Search Intelligence Platform (SIP) Models
# ─────────────────────────────────────────────────────────────

class SearchFeatureStore(Base):
    """Pre-computed feature store for fast offline/online LTR and multi-stage ranking."""
    __tablename__ = 'search_feature_store'

    content_id = Column(Integer, ForeignKey('contents.id'), primary_key=True)
    knowledge_features_json = Column(Text, nullable=True)  # Theme/mood density, fact counts
    popularity_features_json = Column(Text, nullable=True)  # Popularity score, trending velocity
    quality_features_json = Column(Text, nullable=True)  # Rating, completeness score
    graph_features_json = Column(Text, nullable=True)  # Franchise depth, relationship count
    vector_features_json = Column(Text, nullable=True)  # Vector embedding
    updated_at = Column(DateTime, default=datetime.utcnow)


class SearchSession(Base):
    """User search behavior session tracking."""
    __tablename__ = 'search_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=True, index=True)
    query_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class SearchEvent(Base):
    """Detailed search interactions telemetry (queries, clicks, dwell times, reformulations)."""
    __tablename__ = 'search_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(Integer, ForeignKey('search_sessions.id'), nullable=True, index=True)
    query_text = Column(String(512), nullable=False, index=True)
    rewritten_query = Column(String(512), nullable=True)
    parsed_intent = Column(String(50), nullable=False)
    plan_hash = Column(String(64), nullable=True, index=True)
    results_count = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    clicked_content_id = Column(Integer, ForeignKey('contents.id'), nullable=True)
    click_position = Column(Integer, nullable=True)
    dwell_time_seconds = Column(Float, nullable=True)
    event_type = Column(String(50), default="query", index=True)  # query, click, dwell, reformulation, abandonment
    created_at = Column(DateTime, default=datetime.utcnow)


class SearchPlanCache(Base):
    """Cached executable search plans for query optimization."""
    __tablename__ = 'search_plan_cache'

    plan_hash = Column(String(64), primary_key=True)
    query_text = Column(String(512), nullable=False, index=True)
    plan_json = Column(Text, nullable=False)
    hits_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class SynonymDictionary(Base):
    """Managed term expansion dictionary for genres, themes, and abbreviations."""
    __tablename__ = 'synonym_dictionary'

    id = Column(Integer, primary_key=True, autoincrement=True)
    term = Column(String(100), unique=True, nullable=False, index=True)
    expanded_terms_json = Column(Text, nullable=False)  # JSON List[str]
    category = Column(String(50), default="genre")


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
                # Seasons table auto-migrations
                seasons_cols = [c["name"] for c in inspect(self.engine).get_columns("seasons")]
                if "uuid" not in seasons_cols:
                    conn.execute(text("ALTER TABLE seasons ADD COLUMN uuid VARCHAR(36)"))
                if "series_content_id" not in seasons_cols:
                    conn.execute(text("ALTER TABLE seasons ADD COLUMN series_content_id INTEGER"))
                    if "series_id" in seasons_cols:
                        conn.execute(text("UPDATE seasons SET series_content_id = series_id WHERE series_content_id IS NULL"))
                if "air_date" not in seasons_cols:
                    conn.execute(text("ALTER TABLE seasons ADD COLUMN air_date VARCHAR(50)"))
                if "episode_count" not in seasons_cols:
                    conn.execute(text("ALTER TABLE seasons ADD COLUMN episode_count INTEGER DEFAULT 0"))
                if "is_deleted" not in seasons_cols:
                    conn.execute(text("ALTER TABLE seasons ADD COLUMN is_deleted BOOLEAN DEFAULT 0"))

                # Episodes table auto-migrations
                episodes_cols = [c["name"] for c in inspect(self.engine).get_columns("episodes")]
                if "uuid" not in episodes_cols:
                    conn.execute(text("ALTER TABLE episodes ADD COLUMN uuid VARCHAR(36)"))
                if "air_date" not in episodes_cols:
                    conn.execute(text("ALTER TABLE episodes ADD COLUMN air_date VARCHAR(50)"))
                if "still_url" not in episodes_cols:
                    conn.execute(text("ALTER TABLE episodes ADD COLUMN still_url VARCHAR(512)"))
                if "is_deleted" not in episodes_cols:
                    conn.execute(text("ALTER TABLE episodes ADD COLUMN is_deleted BOOLEAN DEFAULT 0"))

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
