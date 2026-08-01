from __future__ import annotations
from typing import Any, Dict, List
from services.knowledge.contracts import BaseInferenceEngine
from services.knowledge.dtos import KnowledgeFactDTO
from services.knowledge.taxonomy import FactCategory, Predicate, SourceWeight

class AudienceEngine(BaseInferenceEngine):
    """
    Infers age suitability ratings and content sensitivity warnings.
    """

    WARNING_KEYWORDS = {
        "violence": ["violence", "blood", "kill", "murder", "combat", "slaughter"],
        "flashing-lights": ["strobe", "flashing", "seizure"],
        "frightening-scenes": ["terror", "nightmare", "horror", "scary", "ghost"],
        "substance-use": ["drug", "alcohol", "addiction", "smuggle"]
    }

    @property
    def engine_name(self) -> str:
        return "AudienceEngine"

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
        text_corpus = (str(content_data.get("overview") or "") + " " + str(content_data.get("tagline") or "")).lower()

        # Age Suitability Inference
        rating = "PG-13"
        genres = [str(g).lower() for g in content_data.get("genres") or []]
        if "animation" in genres or "family" in genres:
            rating = "PG"
        elif any(g in ["horror", "crime"] for g in genres) or "brutal" in text_corpus:
            rating = "R"

        produced.append(KnowledgeFactDTO(
            content_id=content_id,
            category=FactCategory.AUDIENCE_SAFETY.value,
            predicate=Predicate.HAS_SAFETY_WARNING,
            value=f"rating-{rating}",
            confidence=0.90,
            source_weight=SourceWeight.NLP_EXTRACTOR.value,
            source_provider=self.engine_name,
            inference_model="rating_rules_v1",
            model_version=self.model_version
        ))

        # Sensitivity Warning Inference
        for warning, triggers in self.WARNING_KEYWORDS.items():
            if any(t in text_corpus for t in triggers):
                produced.append(KnowledgeFactDTO(
                    content_id=content_id,
                    category=FactCategory.AUDIENCE_SAFETY.value,
                    predicate=Predicate.HAS_SAFETY_WARNING,
                    value=f"warning-{warning}",
                    confidence=0.82,
                    source_weight=SourceWeight.NLP_EXTRACTOR.value,
                    source_provider=self.engine_name,
                    inference_model="warning_keywords_v1",
                    model_version=self.model_version
                ))

        return produced
