from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from services.knowledge.taxonomy import FactCategory, FactState

@dataclass
class KnowledgeFactDTO:
    content_id: int
    category: str
    predicate: str
    value: str
    confidence: float = 1.0
    source_weight: float = 0.80
    state: str = FactState.ACTIVE.value
    superseded_by_id: Optional[int] = None
    retracted_reason: Optional[str] = None
    source_provider: str = "streamora_kip"
    inference_model: str = "baseline_extractor"
    model_version: str = "1.0.0"
    id: Optional[int] = None
    uuid: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class KnowledgeAssertionDTO:
    content_id: int
    assertion_type: str
    subject: str
    relationship: str
    target: str
    confidence: float = 1.0
    id: Optional[int] = None

@dataclass
class KnowledgeRelationshipDTO:
    source_content_id: int
    target_content_id: int
    relationship_type: str  # sequel, prequel, spin_off, shared_universe, thematic_twin
    strength: float = 1.0
    provenance: str = "franchise_engine"
    id: Optional[int] = None

@dataclass
class InferenceRunDTO:
    content_id: int
    engine_name: str
    model_name: str
    model_version: str
    prompt_hash: Optional[str] = None
    execution_time_ms: float = 0.0
    facts_produced: int = 0
    id: Optional[int] = None

@dataclass
class KnowledgeSnapshotDTO:
    content_id: int
    fact_count: int
    knowledge_hash: str
    id: Optional[int] = None
    uuid: Optional[str] = None

@dataclass
class IntelligenceProfileDTO:
    content_id: int
    snapshot_id: Optional[int] = None
    profile_version: str = "1.0.0"
    dominant_themes: List[str] = field(default_factory=list)
    dominant_moods: List[str] = field(default_factory=list)
    pacing: str = "steady"
    narrative_structure: str = "linear"
    audience_rating: str = "PG-13"
    content_warnings: List[str] = field(default_factory=list)
    summary_short: Optional[str] = None
    summary_medium: Optional[str] = None
    summary_deep: Optional[str] = None
    summary_spoiler_free: Optional[str] = None
    overall_confidence: float = 1.0
    fact_count: int = 0

@dataclass
class FranchiseDTO:
    name: str
    slug: str
    description: Optional[str] = None
    backdrop_url: Optional[str] = None
    members: List[Dict] = field(default_factory=list)
    id: Optional[int] = None
