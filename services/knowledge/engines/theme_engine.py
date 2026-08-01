from __future__ import annotations
from typing import Any, Dict, List
from services.knowledge.contracts import BaseInferenceEngine
from services.knowledge.dtos import KnowledgeFactDTO
from services.knowledge.taxonomy import FactCategory, Predicate, SourceWeight

class ThemeEngine(BaseInferenceEngine):
    """
    Infers narrative pacing (fast-paced, slow-burn, steady) and higher-order thematic tropes.
    """

    @property
    def engine_name(self) -> str:
        return "ThemeEngine"

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
        runtime = content_data.get("runtime") or 100

        # Pacing Inference
        genres = [str(g).lower() for g in content_data.get("genres") or []]
        pacing = "steady"
        if any(g in ["action", "thriller", "adventure"] for g in genres) or "chase" in text_corpus:
            pacing = "fast-paced"
        elif any(g in ["drama", "mystery"] for g in genres) and runtime > 120:
            pacing = "slow-burn"

        produced.append(KnowledgeFactDTO(
            content_id=content_id,
            category=FactCategory.NARRATIVE.value,
            predicate=Predicate.HAS_NARRATIVE_TYPE,
            value=f"pacing-{pacing}",
            confidence=0.90,
            source_weight=SourceWeight.NLP_EXTRACTOR.value,
            source_provider=self.engine_name,
            inference_model="pacing_rules_v1",
            model_version=self.model_version
        ))

        # Narrative Structure Inference
        if any(w in text_corpus for w in ["flashback", "timeline", "dream within", "non-linear", "parallel"]):
            produced.append(KnowledgeFactDTO(
                content_id=content_id,
                category=FactCategory.NARRATIVE.value,
                predicate=Predicate.HAS_NARRATIVE_TYPE,
                value="structure-non-linear",
                confidence=0.85,
                source_weight=SourceWeight.NLP_EXTRACTOR.value,
                source_provider=self.engine_name,
                inference_model="structure_rules_v1",
                model_version=self.model_version
            ))

        return produced
