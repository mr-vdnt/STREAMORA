from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class EntityType(Enum):
    """Supported top-level entity types in the Streamora catalog."""

    MOVIE = "movie"
    TV_SERIES = "tvseries"


@dataclass
class RawPayloadDTO:
    """Output of a connector — raw provider data."""

    connector_name: str
    external_id: str
    entity_type: str  # "movie" | "tvseries"
    raw_data: dict
    fetched_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PersonDTO:
    """Normalized person reference."""

    name: str
    role: str  # "actor", "director", "writer", "producer"
    character_name: Optional[str] = None
    profile_url: Optional[str] = None
    order: int = 0


@dataclass
class EpisodeDTO:
    """Normalized episode data."""

    episode_number: int
    title: Optional[str] = None
    overview: Optional[str] = None
    still_url: Optional[str] = None
    runtime: Optional[int] = None
    rating: Optional[float] = None
    air_date: Optional[str] = None


@dataclass
class SeasonDTO:
    """Normalized season data."""

    season_number: int
    title: Optional[str] = None
    overview: Optional[str] = None
    poster_url: Optional[str] = None
    air_date: Optional[str] = None
    episode_count: int = 0
    episodes: List[EpisodeDTO] = field(default_factory=list)


class IngestionState(Enum):
    """Explicit 10-state lifecycle for DAP content processing."""
    DISCOVERED = "DISCOVERED"
    IDENTITY_RESOLVED = "IDENTITY_RESOLVED"
    CANONICAL_ENRICHMENT_PENDING = "CANONICAL_ENRICHMENT_PENDING"
    CANONICAL_ENRICHED = "CANONICAL_ENRICHED"
    VALIDATED = "VALIDATED"
    PERSISTED = "PERSISTED"
    INDEX_PENDING = "INDEX_PENDING"
    INDEXED = "INDEXED"
    READY = "READY"

    # Terminal failure states
    IDENTITY_FAILED = "IDENTITY_FAILED"
    CANONICAL_ENRICHMENT_FAILED = "CANONICAL_ENRICHMENT_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    PERSISTENCE_FAILED = "PERSISTENCE_FAILED"
    INDEXING_FAILED = "INDEXING_FAILED"


@dataclass
class NormalizedContentDTO:
    """Output of the normalizer — canonical shape."""

    external_ids: Dict[str, str]  # {"tmdb": "27205", "imdb": "tt1375666"}
    entity_type: str
    title: str
    original_title: Optional[str] = None
    overview: str = ""
    tagline: Optional[str] = None
    release_date: Optional[str] = None
    runtime: Optional[int] = None
    runtime_seconds: Optional[int] = None  # Canonical runtime in seconds
    language: str = "en"
    genres: List[str] = field(default_factory=list)
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    popularity: float = 0.0
    average_rating: float = 0.0
    vote_count: int = 0
    imdb_rating: Optional[float] = None
    imdb_vote_count: Optional[int] = None
    imdb_url: Optional[str] = None
    cast: List[PersonDTO] = field(default_factory=list)
    crew: List[PersonDTO] = field(default_factory=list)
    # Series-specific
    total_seasons: Optional[int] = None
    total_episodes: Optional[int] = None
    in_production: Optional[bool] = None
    seasons: Optional[List[SeasonDTO]] = None
    # Provenance & Lifecycle
    source_connector: str = ""
    source_payload_hash: str = ""
    provenance: Dict[str, str] = field(default_factory=dict)  # Field-level provider tracking
    enrichment_state: str = IngestionState.DISCOVERED.value


@dataclass
class ResolutionResult:
    """Output of entity resolver."""

    action: str  # "create" | "update" | "skip"
    existing_content_id: Optional[int] = None
    confidence: float = 0.0
    match_signals: List[str] = field(default_factory=list)


@dataclass
class QualityReport:
    """Output of quality scorer."""

    score: float  # 0.0-100.0
    penalties: Dict[str, float] = field(default_factory=dict)
    meets_threshold: bool = True


@dataclass
class ValidationResult:
    """Output of validator."""

    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class PipelineResult:
    """Final result of the ingestion pipeline for a single item."""

    success: bool
    action: str  # "created", "updated", "skipped", "failed"
    content_id: Optional[int] = None
    content_uuid: Optional[str] = None
    quality_score: float = 0.0
    errors: List[str] = field(default_factory=list)
