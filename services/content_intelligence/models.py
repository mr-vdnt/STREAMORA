from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum

class NodeType(str, Enum):
    MOVIE = "MOVIE"
    DIRECTOR = "DIRECTOR"
    ACTOR = "ACTOR"
    GENRE = "GENRE"
    THEME = "THEME"
    KEYWORD = "KEYWORD"

class EdgeType(str, Enum):
    DIRECTED_BY = "DIRECTED_BY"
    ACTED_IN = "ACTED_IN"
    HAS_GENRE = "HAS_GENRE"
    HAS_THEME = "HAS_THEME"
    HAS_KEYWORD = "HAS_KEYWORD"
    SIMILAR_TO = "SIMILAR_TO"
    SHARED_DIRECTOR = "SHARED_DIRECTOR"
    SHARED_ACTOR = "SHARED_ACTOR"
    SHARED_THEME = "SHARED_THEME"

class GraphNode(BaseModel):
    id: str
    type: NodeType
    name: str
    metadata: Dict[str, str] = Field(default_factory=dict)

class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    type: EdgeType
    weight: float = 1.0

class RelationshipConfidence(BaseModel):
    score: float
    confidence: float

class GraphDiagnostics(BaseModel):
    schema_version: str = "1.0"
    graph_revision: int = 1
    build_timestamp: str = ""
    nodes_count: int = 0
    edges_count: int = 0
    adapter_latency_ms: float = 0.0
