from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from services.ingestion.dtos import (
    NormalizedContentDTO,
    QualityReport,
    RawPayloadDTO,
    ResolutionResult,
    ValidationResult,
)


class ConnectorCapability(Enum):
    """Capabilities a connector can declare."""

    SEARCH = "search"
    FETCH_BY_ID = "fetch_by_id"
    TRENDING = "trending"
    DISCOVER = "discover"
    CHANGES = "changes"


@dataclass
class ConnectorManifest:
    """Declares what a connector can do."""

    name: str
    display_name: str
    capabilities: List[ConnectorCapability]
    rate_limit_per_second: float
    supported_entity_types: List[str]


class BaseConnector(ABC):
    """Abstract base class that every data connector must implement."""

    @abstractmethod
    def get_manifest(self) -> ConnectorManifest:
        """Return the connector's capability manifest."""
        ...

    @abstractmethod
    async def fetch_by_id(self, external_id: str, entity_type: str) -> Optional[RawPayloadDTO]:
        """Fetch a single item by its provider-specific ID."""
        ...

    @abstractmethod
    async def fetch_trending(self, entity_type: str, page: int = 1) -> List[RawPayloadDTO]:
        """Fetch trending/popular items."""
        ...

    @abstractmethod
    async def search(self, query: str, entity_type: str = "movie") -> List[RawPayloadDTO]:
        """Search for items by query string."""
        ...

    @abstractmethod
    async def fetch_changes(self, since: datetime) -> List[RawPayloadDTO]:
        """Fetch items that changed since the given timestamp."""
        ...


# --- Pipeline Stage Contracts ---


class MessageType(Enum):
    """Types of messages flowing through the pipeline."""

    RAW_PAYLOAD = "raw_payload"
    VALIDATED = "validated"
    NORMALIZED = "normalized"
    RESOLVED = "resolved"
    CONFLICT_RESOLVED = "conflict_resolved"
    QUALITY_SCORED = "quality_scored"
    WRITTEN = "written"
    FAILED = "failed"


@dataclass
class PipelineMessage:
    """Message that flows between pipeline stages."""

    message_type: MessageType
    job_id: int
    connector_name: str
    external_id: str
    entity_type: str
    payload: Any = None  # Stage-specific payload (DTO or dict)
    raw_payload_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    trace_id: str = ""  # For distributed tracing


class PipelineStage(ABC):
    """Abstract base class for all pipeline stages.

    Each stage consumes a PipelineMessage and emits another PipelineMessage.
    This enables per-stage retry, replay, and future horizontal scaling.
    """

    @property
    @abstractmethod
    def stage_name(self) -> str:
        """Unique identifier for this stage."""
        ...

    @abstractmethod
    async def process(self, message: PipelineMessage) -> PipelineMessage:
        """Process an incoming message and return an outgoing message."""
        ...
