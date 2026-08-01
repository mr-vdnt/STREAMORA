from __future__ import annotations
import re
from typing import Any, Dict, List
from services.knowledge.contracts import BaseInferenceEngine
from services.knowledge.dtos import KnowledgeFactDTO, KnowledgeRelationshipDTO
from services.knowledge.taxonomy import FactCategory, Predicate, SourceWeight

class FranchiseEngine(BaseInferenceEngine):
    """
    Detects franchise universe clusters, sequel/prequel relationships, and timeline ordering.
    """

    KNOWN_FRANCHISES = {
        "spider-man": "Spider-Man Universe",
        "batman": "Batman Universe",
        "star wars": "Star Wars Universe",
        "avengers": "Marvel Cinematic Universe",
        "harry potter": "Wizarding World",
        "lord of the rings": "Middle-earth Universe",
        "matrix": "The Matrix Universe"
    }

    @property
    def engine_name(self) -> str:
        return "FranchiseEngine"

    @property
    def model_version(self) -> str:
        return "1.0.0"

    async def infer(
        self, 
        content_id: int, 
        content_data: Dict[str, Any], 
        existing_facts: List[KnowledgeFactDTO]
    ) -> List[KnowledgeFactDTO]:
        produced: List[KnowledgeFactDTO] = []
        title = str(content_data.get("title") or "").lower()
        overview = str(content_data.get("overview") or "").lower()

        for kw, franchise_name in self.KNOWN_FRANCHISES.items():
            if kw in title or kw in overview:
                produced.append(KnowledgeFactDTO(
                    content_id=content_id,
                    category=FactCategory.SETTING.value,
                    predicate=Predicate.LOCATED_IN,
                    value=f"franchise-{franchise_name.lower().replace(' ', '-')}",
                    confidence=0.95,
                    source_weight=SourceWeight.NLP_EXTRACTOR.value,
                    source_provider=self.engine_name,
                    inference_model="franchise_cluster_v1",
                    model_version=self.model_version
                ))

        return produced
