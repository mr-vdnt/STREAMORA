from __future__ import annotations
import re
from typing import Any, Dict, List, Tuple
from services.search.planner.query_rewriter import QueryRewriteEngine
from services.search.taxonomy import SearchIntent

class QueryIntelligence:
    """
    5-Stage Query Understanding Pipeline:
    1. Normalization & Rewrite
    2. Entity Recognition (Persons, Franchises, Eras)
    3. Intent Detection (Exact Title, Person, Theme/Mood, Similarity, Franchise, Generic)
    4. Constraint Extraction (Genres, Media format, Era)
    5. Ambiguity Resolution
    """

    KNOWN_FRANCHISES = ["spider-man", "batman", "star wars", "avengers", "harry potter", "lord of the rings", "matrix"]
    KNOWN_MOODS = ["mind-bending", "suspenseful", "dark", "heartwarming", "intellectual", "action-packed", "funny"]
    KNOWN_THEMES = ["dream", "space", "time", "crime", "magic", "war", "love", "family", "cyberpunk"]

    def __init__(self):
        self.rewriter = QueryRewriteEngine()

    def process(self, raw_query: str) -> Dict[str, Any]:
        # Stage 1: Normalization & Rewrite
        rewritten = self.rewriter.rewrite(raw_query)
        clean_lower = rewritten.lower()

        # Stage 2: Entity Recognition
        extracted_entities = {
            "persons": [],
            "franchises": [],
            "eras": []
        }

        for f in self.KNOWN_FRANCHISES:
            if f in clean_lower:
                extracted_entities["franchises"].append(f.title())

        # Era extraction (e.g. 90s, 80s, 2010s)
        era_match = re.search(r'\b(19\d0|20\d0|80|90)s?\b', clean_lower)
        if era_match:
            extracted_entities["eras"].append(era_match.group(0))

        # Stage 3: Intent Detection
        intent = SearchIntent.GENERIC_SEARCH.value

        if "like " in clean_lower or "similar to " in clean_lower:
            intent = SearchIntent.SIMILARITY_QUERY.value
        elif extracted_entities["franchises"]:
            intent = SearchIntent.FRANCHISE_QUERY.value
        elif any(m in clean_lower for m in self.KNOWN_MOODS) or any(t in clean_lower for t in self.KNOWN_THEMES):
            intent = SearchIntent.THEME_MOOD_QUERY.value
        elif len(clean_lower.split()) <= 3 and not any(w in clean_lower for w in ["movie", "series", "funny", "best"]):
            intent = SearchIntent.EXACT_TITLE.value

        # Stage 4: Constraint Extraction
        entity_type_filter = None
        if "movie" in clean_lower or "film" in clean_lower:
            entity_type_filter = "movie"
        elif "series" in clean_lower or "show" in clean_lower or "tv" in clean_lower:
            entity_type_filter = "tvseries"

        extracted_moods = [m for m in self.KNOWN_MOODS if m in clean_lower]
        extracted_themes = [t for t in self.KNOWN_THEMES if t in clean_lower]

        return {
            "raw_query": raw_query,
            "rewritten_query": rewritten,
            "intent": intent,
            "extracted_entities": extracted_entities,
            "extracted_moods": extracted_moods,
            "extracted_themes": extracted_themes,
            "entity_type_filter": entity_type_filter
        }
