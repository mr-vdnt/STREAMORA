from enum import Enum


class SearchIntent(Enum):
    EXACT_TITLE = "exact_title"
    PERSON_SEARCH = "person_search"
    THEME_MOOD_QUERY = "theme_mood_query"
    SIMILARITY_QUERY = "similarity_query"
    FRANCHISE_QUERY = "franchise_query"
    GENERIC_SEARCH = "generic_search"


class RetrievalStrategy(Enum):
    LEXICAL = "lexical"
    KNOWLEDGE_FACT = "knowledge_fact"
    RELATIONSHIP = "relationship"
    FRANCHISE = "franchise"
    EMBEDDING = "embedding"
