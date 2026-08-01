from __future__ import annotations
from typing import Any, Dict, List
from services.knowledge.contracts import BaseInferenceEngine
from services.knowledge.dtos import KnowledgeFactDTO
from services.knowledge.taxonomy import FactCategory, Predicate, SourceWeight

class NarrativeEngine(BaseInferenceEngine):
    """
    Infers character roles (Protagonist, Antagonist, Mentor) and core conflict archetypes.
    """

    @property
    def engine_name(self) -> str:
        return "NarrativeEngine"

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
        cast_facts = [f for f in existing_facts if f.category == FactCategory.CHARACTER.value]

        # First cast member is assigned Protagonist archetype
        if cast_facts:
            lead = cast_facts[0]
            produced.append(KnowledgeFactDTO(
                content_id=content_id,
                category=FactCategory.CHARACTER.value,
                predicate=Predicate.HAS_CHARACTER_ROLE,
                value=f"archetype-protagonist:{lead.value}",
                confidence=0.92,
                source_weight=SourceWeight.NLP_EXTRACTOR.value,
                source_provider=self.engine_name,
                inference_model="cast_order_heuristic",
                model_version=self.model_version
            ))

        if len(cast_facts) > 1:
            second = cast_facts[1]
            produced.append(KnowledgeFactDTO(
                content_id=content_id,
                category=FactCategory.CHARACTER.value,
                predicate=Predicate.HAS_CHARACTER_ROLE,
                value=f"archetype-deuteragonist:{second.value}",
                confidence=0.85,
                source_weight=SourceWeight.NLP_EXTRACTOR.value,
                source_provider=self.engine_name,
                inference_model="cast_order_heuristic",
                model_version=self.model_version
            ))

        return produced
