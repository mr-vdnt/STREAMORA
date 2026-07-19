import re
import json
import string
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import functools

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
                norm_title = re.sub(r'[^\w\s-]', '', title).strip()
                self.known_titles[norm_title] = row.get('title', '')
                
            for actor in str(row.get('cast', '')).split(','):
                a = re.sub(r'[^\w\s-]', '', actor.strip().lower()).strip()
                if a: self.known_actors.add(a)
                
            for director in str(row.get('director', '')).split(','):
                d = re.sub(r'[^\w\s-]', '', director.strip().lower()).strip()
                if d: self.known_directors.add(d)
                
            for genre in str(row.get('genres', '')).split('|'):
                g = re.sub(r'[^\w\s-]', '', genre.strip().lower()).strip()
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
        """Sliding window entity extraction using O(1) dictionary lookups."""
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
            
        words = text.split()
        
        def generate_ngrams(words, max_n=6):
            # Yields (gram, start_idx, end_idx) descending by length
            for n in range(max_n, 0, -1):
                for i in range(len(words) - n + 1):
                    if all(w is not None for w in words[i:i+n]):
                        yield " ".join(words[i:i+n]), i, i+n

        # 1. Extract exact titles
        for gram, i, j in generate_ngrams(words, max_n=6):
            if gram in self.known_titles:
                entities["reference_title"] = self.known_titles[gram]
                for k in range(i, j): words[k] = None
                break # Only grab the first primary reference title

        # 2. Extract Actors & Directors
        for gram, i, j in generate_ngrams(words, max_n=4):
            if gram in self.known_actors:
                entities["actors"].append(gram.title())
                for k in range(i, j): words[k] = None
            elif gram in self.known_directors:
                entities["directors"].append(gram.title())
                for k in range(i, j): words[k] = None

        # 3. Extract Aliases, Genres, Moods, Temporal
        for gram, i, j in generate_ngrams(words, max_n=3):
            if gram in self.dictionaries["genre_aliases"]:
                entities["genres"].append(self.dictionaries["genre_aliases"][gram].title())
                for k in range(i, j): words[k] = None
                
        for w in words:
            if w is None: continue
            if w in self.known_genres:
                entities["genres"].append(w.title())
            if w in self.dictionaries["moods"]:
                entities["themes"].append(w)
            if w in self.dictionaries["temporal_modifiers"]:
                entities["temporal"].append(self.dictionaries["temporal_modifiers"][w])

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

    def _generate_fingerprint(self, intent: str, entities: dict, filters: dict) -> str:
        parts = []
        if intent == "recommendation": parts.append("REC")
        elif intent == "search": parts.append("SEARCH")
        elif intent == "trending": parts.append("TREND")
        elif intent == "explain": parts.append("EXPL")
        else: parts.append("CHAT")
        
        if entities.get("reference_title"): parts.append("REF")
        if entities.get("actors"): parts.append("ACT")
        if entities.get("directors"): parts.append("DIR")
        if entities.get("genres"): parts.append("GEN")
        if entities.get("themes"): parts.append("THEME")
        
        if filters.get("year_min") or filters.get("year_max"): parts.append("YEAR")
        if filters.get("runtime_max"): parts.append("RUN")
        
        return "_".join(parts) if parts else "UNKNOWN"

    def _determine_priority(self, entities: dict) -> list[str]:
        priority = []
        if entities.get("reference_title"): priority.append("reference_movie")
        if entities.get("directors"): priority.append("director")
        if entities.get("actors"): priority.append("actor")
        if entities.get("genres"): priority.append("genre")
        if entities.get("themes"): priority.append("theme")
        return priority

    def _validate_constraints(self, filters: dict):
        if "year_min" in filters:
            filters["year_min"] = max(1888, filters["year_min"])
        if "year_max" in filters:
            filters["year_max"] = min(2050, filters["year_max"])
            if "year_min" in filters and filters["year_min"] > filters["year_max"]:
                filters.pop("year_min")
        if "runtime_max" in filters:
            if "year_min" in filters and filters["year_min"] > filters["year_max"]: filters.pop("year_min")
        if "runtime_max" in filters: filters["runtime_max"] = max(10, filters["runtime_max"])

    @functools.lru_cache(maxsize=1024)
    def _parse_cached(self, query: str) -> str:
        norm_query = self._normalize(query)
        tokens = self._tokenize_and_lemmatize(norm_query)
        intent = self._extract_intent(tokens)
        pos_query, neg_query = self._parse_negative_filters(norm_query)
        entities = self._extract_entities(pos_query)
        filters = self._build_constraints(norm_query, neg_query)
        self._validate_constraints(filters)
        plan = self._determine_query_plan(intent, entities, filters)
        priority = self._determine_priority(entities)
        fingerprint = self._generate_fingerprint(intent, entities, filters)
        
        confidence = {}
        for p in priority: confidence[p] = 1.0
        
        result = {
            "schema_version": "1.0",
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
            "priority": priority,
            "query_plan": plan,
            "fingerprint": fingerprint,
            "debug": {
                "entity_confidence": confidence
            }
        }
        return json.dumps(result)

    def parse(self, query: str, context: dict = None) -> dict:
        """
        Main pipeline entrypoint.
        Translates query into structured JSON object using LRU cache.
        """
        cached_str = self._parse_cached(query)
        result = json.loads(cached_str)
        
        if context:
            entities = result["entities"]
            if not entities["directors"] and context.get("directors"):
                entities["directors"] = context["directors"]
            if not entities["actors"] and context.get("actors"):
                entities["actors"] = context["actors"]
            if not entities["genres"] and context.get("genres"):
                entities["genres"] = context["genres"]
                
        return result
