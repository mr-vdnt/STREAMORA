from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional

class FeatureValueType(Enum):
    FLOAT = "float"
    INT = "int"
    STRING = "string"
    VECTOR = "vector"
    MAP = "map"

@dataclass
class FeatureDefinition:
    name: str
    entity_type: str  # "content", "user"
    value_type: FeatureValueType
    description: str
    default_value: Any

class EnterpriseFeatureRegistry:
    """Unified Enterprise Feature Registry mapping feature definitions across Search, Recommendation, Hero, and Discovery."""

    def __init__(self):
        self._definitions: Dict[str, FeatureDefinition] = {}
        self._register_default_features()

    def register_feature(self, definition: FeatureDefinition):
        self._definitions[definition.name] = definition

    def get_feature(self, name: str) -> Optional[FeatureDefinition]:
        return self._definitions.get(name)

    def list_features(self, entity_type: Optional[str] = None) -> List[FeatureDefinition]:
        if entity_type:
            return [f for f in self._definitions.values() if f.entity_type == entity_type]
        return list(self._definitions.values())

    def _register_default_features(self):
        # Content Features
        self.register_feature(FeatureDefinition("popularity_score", "content", FeatureValueType.FLOAT, "Normalized 0-1 popularity score", 0.5))
        self.register_feature(FeatureDefinition("quality_rating", "content", FeatureValueType.FLOAT, "Average rating 0-10", 7.5))
        self.register_feature(FeatureDefinition("freshness_score", "content", FeatureValueType.FLOAT, "Decay score based on release date", 0.8))
        self.register_feature(FeatureDefinition("knowledge_fact_count", "content", FeatureValueType.INT, "Number of atomic facts extracted", 10))
        self.register_feature(FeatureDefinition("embedding_vector", "content", FeatureValueType.VECTOR, "Dense semantic embedding vector", [0.1] * 128))
        
        # User Features
        self.register_feature(FeatureDefinition("genre_affinities", "user", FeatureValueType.MAP, "User genre affinity map", {"Sci-Fi": 0.9, "Action": 0.8}))
        self.register_feature(FeatureDefinition("theme_affinities", "user", FeatureValueType.MAP, "User narrative theme affinity map", {"dream": 0.95}))
        self.register_feature(FeatureDefinition("completion_rate", "user", FeatureValueType.FLOAT, "Historical watch completion percentage", 0.85))
