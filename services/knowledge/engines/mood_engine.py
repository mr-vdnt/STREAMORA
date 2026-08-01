from __future__ import annotations
from typing import Any, Dict, List
from services.knowledge.contracts import BaseInferenceEngine
from services.knowledge.dtos import KnowledgeFactDTO
from services.knowledge.taxonomy import FactCategory, Predicate, SourceWeight

class MoodEngine(BaseInferenceEngine):
    """
    Infers emotional tone & moods (suspenseful, mind-bending, heartwarming, dark, intellectual, action-packed).
    """

    MOOD_TRIGGERS = {
        "mind-bending": ["dream", "subconscious", "reality", "illusion", "quantum", "memory", "hallucination"],
        "suspenseful": ["thriller", "mystery", "crime", "detective", "suspense", "murder", "trap", "secret"],
        "dark": ["dark", "horrible", "sinister", "goth", "grim", "death", "brutal"],
        "heartwarming": ["family", "love", "friendship", "kindness", "warmth", "journey", "reunion"],
        "intellectual": ["philosophy", "truth", "science", "mind", "chess", "genius", "discovery"],
        "action-packed": ["explosion", "battle", "war", "chase", "combat", "agent", "assassin"]
    }

    @property
    def engine_name(self) -> str:
        return "MoodEngine"

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

        for fact in existing_facts:
            text_corpus += " " + str(fact.value).lower()

        detected_moods = set()
        for mood, triggers in self.MOOD_TRIGGERS.items():
            if any(t in text_corpus for t in triggers):
                detected_moods.add(mood)

        for mood in detected_moods:
            produced.append(KnowledgeFactDTO(
                content_id=content_id,
                category=FactCategory.MOOD.value,
                predicate=Predicate.HAS_MOOD,
                value=mood,
                confidence=0.88,
                source_weight=SourceWeight.NLP_EXTRACTOR.value,
                source_provider=self.engine_name,
                inference_model="mood_heuristic_v1",
                model_version=self.model_version
            ))

        return produced
