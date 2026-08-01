from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass
class SearchQueryDTO:
    raw_query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    entity_type_filter: Optional[str] = None  # "movie", "tvseries"
    genre_filter: Optional[str] = None
    limit: int = 20
    offset: int = 0


@dataclass
class SearchPlanDTO:
    query_text: str
    rewritten_query: str
    intent: str  # SearchIntent value
    extracted_entities: Dict[str, List[str]] = field(default_factory=dict)  # {"persons": [], "franchises": [], "eras": []}
    target_themes: List[str] = field(default_factory=list)
    target_moods: List[str] = field(default_factory=list)
    active_retrievers: List[str] = field(default_factory=list)  # ["lexical", "knowledge_fact", ...]
    estimated_cost: float = 1.0
    estimated_recall: float = 0.90
    latency_budget_ms: float = 50.0
    plan_hash: str = ""


@dataclass
class RetrievedCandidateDTO:
    content_id: int
    retriever_name: str
    score: float
    retrieval_reason: str
    provenance_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RankingFeatureVectorDTO:
    content_id: int
    lexical_score: float = 0.0
    knowledge_overlap_score: float = 0.0
    popularity_score: float = 0.0
    quality_score: float = 0.0
    freshness_score: float = 0.0
    vector_similarity: float = 0.0
    final_rank_score: float = 0.0


@dataclass
class ExplanationNodeDTO:
    source: str  # "Lexical", "Knowledge", "Relationship", "Popularity"
    feature: str  # "Theme: Dream", "Cast: Leonardo DiCaprio"
    score: float
    weight: float
    description: str


@dataclass
class SearchResultItemDTO:
    content_id: int
    title: str
    slug: str
    entity_type: str
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    rating: float = 0.0
    popularity: float = 0.0
    release_date: Optional[str] = None
    rank_score: float = 0.0
    matched_sources: List[str] = field(default_factory=list)
    explanations: List[ExplanationNodeDTO] = field(default_factory=list)


@dataclass
class SearchResponseDTO:
    query_text: str
    intent: str
    plan_hash: str
    total_hits: int
    latency_ms: float
    results: List[SearchResultItemDTO] = field(default_factory=list)


@dataclass
class AutocompleteCategoryDTO:
    category: str  # "titles", "persons", "franchises", "themes", "moods"
    items: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AutocompleteResponseDTO:
    query: str
    categories: List[AutocompleteCategoryDTO] = field(default_factory=list)
