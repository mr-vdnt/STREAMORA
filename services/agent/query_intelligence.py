import re
import json
import string
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Ensure NLTK dependencies are available
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    nltk.download('wordnet', quiet=True)

class QueryIntelligenceEngine:
    """
    Deterministic NLP Pipeline for parsing user search intent.
    Translates natural language into a structured constraints object.
    Does not use LLMs.
    """
    
    def __init__(self, movies_db: dict):
        self.lemmatizer = WordNetLemmatizer()
        
        # Load Entities from the Catalog
        self.known_actors = set()
        self.known_directors = set()
        self.known_genres = set()
        self.known_titles = {} # lowercase -> actual title
        
        for iid, row in movies_db.items():
            title = str(row.get('title', '')).lower()
            if title:
                self.known_titles[title] = row.get('title', '')
                
            for actor in str(row.get('cast', '')).split(','):
                a = actor.strip().lower()
                if a: self.known_actors.add(a)
                
            for director in str(row.get('director', '')).split(','):
                d = director.strip().lower()
                if d: self.known_directors.add(d)
                
            for genre in str(row.get('genres', '')).split('|'):
                g = genre.strip().lower()
                if g: self.known_genres.add(g)

        # Build Synonym Dictionaries
        self.dictionaries = {
            "intent_recommendation": ["recommend", "suggest", "show", "find", "discover", "watch", "similar", "like", "give"],
            "intent_explain": ["explain", "why", "meaning", "ending", "summarize", "plot"],
            "intent_trending": ["trending", "popular", "top", "hottest", "viral"],
            
            "moods": ["dark", "funny", "sad", "uplifting", "mind-bending", "psychological", "feel-good", "scary", "romantic", "intense", "epic", "gritty"],
            "temporal_modifiers": {
                "latest": "recent",
                "recent": "recent",
                "new": "recent",
                "old": "classic",
                "classic": "classic",
                "90s": "1990s",
                "80s": "1980s",
                "2000s": "2000s"
            },
            
            "genre_aliases": {
                "sci fi": "science fiction",
                "sci-fi": "science fiction",
                "rom com": "romance",
                "rom-com": "romance",
                "fun": "comedy",
                "scary": "horror"
            }
        }

    def _normalize(self, query: str) -> str:
        # Lowercase and remove punctuation except hyphens
        q = query.lower()
        q = re.sub(r'[^\w\s-]', '', q)
        return q.strip()

    def _tokenize_and_lemmatize(self, query: str) -> list[str]:
        tokens = word_tokenize(query)
        # Lemmatize helps group words like "movies", "films" -> "movie", "film"
        return [self.lemmatizer.lemmatize(t) for t in tokens]

    def _extract_intent(self, tokens: list[str]) -> str:
        for t in tokens:
            if t in self.dictionaries["intent_explain"]:
                return "explain"
            if t in self.dictionaries["intent_recommendation"]:
                return "recommendation"
            if t in self.dictionaries["intent_trending"]:
                return "trending"
        
        # Default fallback intent if not explicitly conversation
        chat_greetings = {"hi", "hello", "hey", "sup", "how"}
        if len(tokens) <= 3 and any(t in chat_greetings for t in tokens):
            return "chat"
            
        return "search"

    def _parse_negative_filters(self, query: str) -> tuple[str, str]:
        """Splits query into positive and negative parts."""
        # Simple split on exclusion markers
        markers = [r"\bwithout\b", r"\bbut not\b", r"\bexcept\b", r"\bnot\b"]
        pattern = "|".join(markers)
        
        parts = re.split(pattern, query, maxsplit=1)
        if len(parts) > 1:
            return parts[0].strip(), parts[1].strip()
        return query, ""

    def _extract_entities(self, text: str) -> dict:
        """Sliding window entity extraction across known sets."""
        entities = {
            "actors": [],
            "directors": [],
            "genres": [],
            "themes": [],
            "reference_title": None,
            "temporal": []
        }
        
        if not text:
            return entities

        # 1. Extract exact titles (Multi-word search requires greedy matching)
        # Sort known titles by length descending so we match "The Lord of the Rings" before "The Lord"
        sorted_titles = sorted(self.known_titles.keys(), key=lambda x: len(x), reverse=True)
        text_for_titles = text
        for t in sorted_titles:
            if re.search(r'\b' + re.escape(t) + r'\b', text_for_titles):
                entities["reference_title"] = self.known_titles[t]
                # Blank it out so we don't double extract parts of the title
                text_for_titles = re.sub(r'\b' + re.escape(t) + r'\b', '', text_for_titles)
                break # Only grab the first primary reference title

        # 2. Extract Multi-word entities (Actors, Directors)
        text_for_entities = text_for_titles
        for a in sorted(self.known_actors, key=lambda x: len(x), reverse=True):
            if re.search(r'\b' + re.escape(a) + r'\b', text_for_entities):
                entities["actors"].append(a.title())
                text_for_entities = re.sub(r'\b' + re.escape(a) + r'\b', '', text_for_entities)
                
        for d in sorted(self.known_directors, key=lambda x: len(x), reverse=True):
            if re.search(r'\b' + re.escape(d) + r'\b', text_for_entities):
                entities["directors"].append(d.title())
                text_for_entities = re.sub(r'\b' + re.escape(d) + r'\b', '', text_for_entities)

        # 3. Extract single-word properties (Genres, Moods, Temporal) via tokens
        tokens = word_tokenize(text_for_entities)
        
        # Check aliases first
        for alias, real_genre in self.dictionaries["genre_aliases"].items():
            if alias in text_for_entities:
                entities["genres"].append(real_genre.title())
                text_for_entities = text_for_entities.replace(alias, "")

        for t in tokens:
            if t in self.known_genres:
                entities["genres"].append(t.title())
            if t in self.dictionaries["moods"]:
                entities["themes"].append(t)
            if t in self.dictionaries["temporal_modifiers"]:
                entities["temporal"].append(self.dictionaries["temporal_modifiers"][t])

        # Deduplicate
        entities["genres"] = list(set(entities["genres"]))
        entities["themes"] = list(set(entities["themes"]))
        
        return entities

    def _build_constraints(self, positive_text: str, negative_text: str) -> dict:
        filters = {}
        
        # Parse positive temporal constraints (e.g., "after 2015", "under 2 hours")
        year_min_match = re.search(r'(?:after|>|since)\s*(\d{4})', positive_text)
        year_max_match = re.search(r'(?:before|<|until)\s*(\d{4})', positive_text)
        runtime_max_match = re.search(r'(?:under|<)\s*(\d+)\s*hour', positive_text)
        
        if year_min_match:
            filters["year_min"] = int(year_min_match.group(1))
        if year_max_match:
            filters["year_max"] = int(year_max_match.group(1))
        if runtime_max_match:
            filters["runtime_max"] = int(runtime_max_match.group(1)) * 60

        # Parse exclusions from the negative part of the query
        if negative_text:
            neg_entities = self._extract_entities(negative_text)
            if neg_entities["genres"]:
                filters["exclude_genres"] = neg_entities["genres"]
            if neg_entities["actors"]:
                filters["exclude_actors"] = neg_entities["actors"]
                
        return filters

    def _determine_query_plan(self, intent: str, entities: dict, filters: dict) -> str:
        if intent == "explain":
            return "explain"
        if intent == "chat":
            return "chat"
            
        has_entities = bool(entities["actors"] or entities["directors"] or entities["genres"] or entities["reference_title"])
        has_filters = bool(filters)
        has_themes = bool(entities["themes"])
        
        if has_themes or (intent == "recommendation" and not has_entities and not has_filters):
            return "semantic_recommendation"
            
        if has_entities or has_filters:
            return "deterministic_search"
            
        return "semantic_recommendation" # Default fallback for vague queries

    def parse(self, query: str, context: dict = None) -> dict:
        """
        Main pipeline entrypoint.
        Translates query into structured JSON object.
        """
        # 1. Normalize
        norm_query = self._normalize(query)
        
        # 2. Tokenize & Lemmatize
        tokens = self._tokenize_and_lemmatize(norm_query)
        
        # 3. Detect Intent
        intent = self._extract_intent(tokens)
        
        # 4. Split Exclusions
        pos_query, neg_query = self._parse_negative_filters(norm_query)
        
        # 5. Extract Entities
        entities = self._extract_entities(pos_query)
        
        # 6. Session Context Merge
        if context:
            if not entities["directors"] and context.get("directors"):
                entities["directors"] = context["directors"]
            if not entities["actors"] and context.get("actors"):
                entities["actors"] = context["actors"]
            if not entities["genres"] and context.get("genres"):
                entities["genres"] = context["genres"]
                
        # 7. Build Constraints
        filters = self._build_constraints(norm_query, neg_query)
        
        # 8. Query Plan
        plan = self._determine_query_plan(intent, entities, filters)
        
        # 9. Return Contract
        return {
            "intent": intent,
            "reference_title": entities["reference_title"],
            "entities": {
                "actors": entities["actors"],
                "directors": entities["directors"],
                "genres": entities["genres"],
                "themes": entities["themes"],
                "temporal": entities["temporal"]
            },
            "filters": filters,
            "query_plan": plan
        }
