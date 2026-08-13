"""
Theme & Mood Extractor for Streamora Knowledge & Intelligence Platform (KIP).

Extracts atomic KnowledgeFacts from content metadata:
- Themes (has_theme)
- Moods (has_mood)
- Tropes (has_trope)
- Narrative structure (has_narrative_type)
"""
from typing import Any, Dict, List
from services.knowledge.contracts import BaseInferenceEngine
from services.knowledge.dtos import KnowledgeFactDTO
from services.knowledge.taxonomy import FactCategory, Predicate, SourceWeight


class ThemeMoodExtractor(BaseInferenceEngine):
    """Inference engine that extracts atomic theme, mood, and trope facts."""

    @property
    def engine_name(self) -> str:
        return "theme_mood_extractor"

    @property
    def model_version(self) -> str:
        return "1.0.0"

    async def infer(
        self,
        content_id: int,
        content_data: Dict[str, Any],
        existing_facts: List[KnowledgeFactDTO]
    ) -> List[KnowledgeFactDTO]:
        facts: List[KnowledgeFactDTO] = []
        overview = content_data.get("overview", "").lower()
        genres = [g.lower() for g in content_data.get("genres", [])]

        # Theme Inference Rules
        theme_mappings = {
            "space": "Space Exploration",
            "time travel": "Time Travel",
            "ai": "Artificial Intelligence",
            "robot": "Artificial Intelligence",
            "dream": "Subconscious Mind",
            "multiverse": "Alternate Realities",
            "superhero": "Heroic Journey",
            "crime": "Moral Ambiguity",
            "mafia": "Organized Crime",
            "dystopia": "Dystopian Future"
        }
        for kw, theme in theme_mappings.items():
            if kw in overview:
                facts.append(KnowledgeFactDTO(
                    content_id=content_id,
                    category=FactCategory.THEME.value,
                    predicate=Predicate.HAS_THEME,
                    value=theme,
                    confidence=0.85,
                    source_weight=SourceWeight.get_weight("nlp_extractor"),
                    inference_model=self.engine_name,
                    model_version=self.model_version
                ))

        # Mood Inference Rules based on genres & overview keywords
        mood_rules = [
            ("action", "Adrenaline-Fueled"),
            ("thriller", "Tense & Suspenseful"),
            ("comedy", "Lighthearted & Funny"),
            ("horror", "Dark & Terrifying"),
            ("drama", "Emotional & Thought-Provoking"),
            ("sci-fi", "Mind-Bending & Imaginative")
        ]
        for genre_kw, mood in mood_rules:
            if genre_kw in genres or genre_kw in overview:
                facts.append(KnowledgeFactDTO(
                    content_id=content_id,
                    category=FactCategory.MOOD.value,
                    predicate=Predicate.HAS_MOOD,
                    value=mood,
                    confidence=0.90,
                    source_weight=SourceWeight.get_weight("imdb"),
                    inference_model=self.engine_name,
                    model_version=self.model_version
                ))

        # Narrative Trope Rules
        trope_rules = [
            ("chosen one", "The Chosen One"),
            ("heist", "The Big Heist"),
            ("revenge", "Revenge Quest"),
            ("unreliable narrator", "Unreliable Narrator")
        ]
        for kw, trope in trope_rules:
            if kw in overview:
                facts.append(KnowledgeFactDTO(
                    content_id=content_id,
                    category=FactCategory.TROPE.value,
                    predicate=Predicate.HAS_TROPE,
                    value=trope,
                    confidence=0.80,
                    source_weight=SourceWeight.get_weight("nlp_extractor"),
                    inference_model=self.engine_name,
                    model_version=self.model_version
                ))

        return facts
