from enum import Enum
from typing import Dict

class FactCategory(Enum):
    THEME = "theme"
    MOOD = "mood"
    SETTING = "setting"
    TOPIC = "topic"
    TROPE = "trope"
    CHARACTER = "character"
    OBJECT = "object"
    NARRATIVE = "narrative"
    AUDIENCE_SAFETY = "audience_safety"

class FactState(Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    RETRACTED = "RETRACTED"
    EXPIRED = "EXPIRED"

class SourceWeight(Enum):
    MANUAL_CURATOR = 1.00
    IMDB = 0.85
    TMDB = 0.80
    NLP_EXTRACTOR = 0.70
    LLM_INFERENCE = 0.65
    DEFAULT = 0.75

    @classmethod
    def get_weight(cls, source_name: str) -> float:
        s = source_name.lower().strip()
        if "curator" in s:
            return cls.MANUAL_CURATOR.value
        elif "imdb" in s:
            return cls.IMDB.value
        elif "tmdb" in s:
            return cls.TMDB.value
        elif "nlp" in s:
            return cls.NLP_EXTRACTOR.value
        elif "llm" in s:
            return cls.LLM_INFERENCE.value
        return cls.DEFAULT.value

class Predicate:
    HAS_THEME = "has_theme"
    HAS_MOOD = "has_mood"
    LOCATED_IN = "located_in"
    HAS_TOPIC = "has_topic"
    HAS_TROPE = "has_trope"
    HAS_CHARACTER_ROLE = "has_character_role"
    FEATURES_OBJECT = "features_object"
    HAS_NARRATIVE_TYPE = "has_narrative_type"
    HAS_SAFETY_WARNING = "has_safety_warning"
