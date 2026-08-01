from __future__ import annotations
import re
from typing import Any, Dict, List
from services.knowledge.taxonomy import FactCategory, Predicate, FactState, SourceWeight
from services.knowledge.dtos import KnowledgeFactDTO

class KnowledgeExtractor:
    """
    Baseline Knowledge Extractor.
    Extracts atomic KnowledgeFacts from canonical content metadata (title, overview, genres, cast, release_date).
    """

    KEYWORD_THEME_MAP = {
        "dream": "dream-manipulation",
        "subconscious": "subconscious-mind",
        "time": "time-dilation",
        "future": "futuristic-setting",
        "space": "space-exploration",
        "robot": "artificial-intelligence",
        "ai": "artificial-intelligence",
        "cyber": "cyberpunk",
        "magic": "magic-and-wizardry",
        "hero": "superheroic-journey",
        "crime": "organized-crime",
        "police": "law-enforcement",
        "detective": "investigation",
        "war": "military-conflict",
        "love": "romantic-relationship",
        "family": "family-bonds",
        "survival": "survival-instinct",
        "revenge": "vengeance"
    }

    def extract_baseline_facts(self, content_id: int, content_data: Dict[str, Any]) -> List[KnowledgeFactDTO]:
        facts: List[KnowledgeFactDTO] = []

        overview = str(content_data.get("overview") or "").lower()
        title = str(content_data.get("title") or "")
        genres = content_data.get("genres") or []
        release_date = str(content_data.get("release_date") or "")
        cast = content_data.get("cast") or []

        # 1. Extract Genre-based Themes
        for genre in genres:
            genre_clean = str(genre).lower().strip()
            facts.append(KnowledgeFactDTO(
                content_id=content_id,
                category=FactCategory.THEME.value,
                predicate=Predicate.HAS_THEME,
                value=f"genre-{genre_clean}",
                confidence=0.95,
                source_weight=SourceWeight.TMDB.value,
                source_provider="metadata_extractor",
                inference_model="baseline_genre_rule",
                model_version="1.0.0"
            ))

        # 2. Extract Keyword Themes from Overview Text
        words = re.findall(r'\b\w+\b', overview)
        seen_keywords = set()
        for word in words:
            if word in self.KEYWORD_THEME_MAP and word not in seen_keywords:
                seen_keywords.add(word)
                theme_val = self.KEYWORD_THEME_MAP[word]
                facts.append(KnowledgeFactDTO(
                    content_id=content_id,
                    category=FactCategory.TOPIC.value,
                    predicate=Predicate.HAS_TOPIC,
                    value=theme_val,
                    confidence=0.85,
                    source_weight=SourceWeight.NLP_EXTRACTOR.value,
                    source_provider="nlp_extractor",
                    inference_model="keyword_matcher",
                    model_version="1.0.0"
                ))

        # 3. Extract Setting / Era facts from Release Date
        if release_date and len(release_date) >= 4:
            year_str = release_date[:4]
            if year_str.isdigit():
                year = int(year_str)
                decade = (year // 10) * 10
                facts.append(KnowledgeFactDTO(
                    content_id=content_id,
                    category=FactCategory.SETTING.value,
                    predicate=Predicate.LOCATED_IN,
                    value=f"release-decade-{decade}s",
                    confidence=1.0,
                    source_weight=SourceWeight.TMDB.value,
                    source_provider="metadata_extractor",
                    inference_model="date_parser",
                    model_version="1.0.0"
                ))

        # 4. Extract Character & Cast Role Facts
        for idx, person in enumerate(cast[:10]):
            name = person.get("name") if isinstance(person, dict) else str(person)
            role = person.get("character_name") if isinstance(person, dict) else None
            if name:
                char_val = f"{name} as {role}" if role else name
                facts.append(KnowledgeFactDTO(
                    content_id=content_id,
                    category=FactCategory.CHARACTER.value,
                    predicate=Predicate.HAS_CHARACTER_ROLE,
                    value=char_val,
                    confidence=0.90,
                    source_weight=SourceWeight.TMDB.value,
                    source_provider="metadata_extractor",
                    inference_model="cast_indexer",
                    model_version="1.0.0"
                ))

        return facts
