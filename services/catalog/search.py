import re
import unicodedata
from thefuzz import fuzz
from typing import List, Dict, Any, Optional

# Alias mappings (simplified dictionary)
ALIASES = {
    "lotr": "the lord of the rings",
    "avengers 1": "the avengers",
    "infinity war": "avengers: infinity war",
    "star wars 4": "star wars: episode iv - a new hope",
    "harry potter 1": "harry potter and the sorcerer's stone",
    "sci fi": "science fiction",
}

class DeterministicSearchEngine:
    def __init__(self, movies_db: Dict[int, dict]):
        self.movies_db = movies_db

    def normalize(self, text: str) -> str:
        """
        Normalize: Case, Whitespace, Unicode, Apostrophes, Accents, Symbols, Hyphens
        """
        if not text:
            return ""
        # Unicode normalization to remove accents
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
        # Lowercase
        text = text.lower()
        # Remove apostrophes
        text = text.replace("'", "").replace("’", "")
        # Replace hyphens with space
        text = text.replace("-", " ")
        # Keep only alphanumeric and spaces
        text = re.sub(r'[^a-z0-9\s]', '', text)
        # Normalize whitespace
        text = " ".join(text.split())
        return text

    def extract_entities(self, query: str) -> Dict[str, List[str]]:
        """
        Extract deterministic entities (Actors, Directors, Genres, Years) from query.
        """
        norm_query = self.normalize(query)
        entities = {
            "actors": [],
            "directors": [],
            "genres": [],
            "years": []
        }
        
        # Extremely simplified entity extraction based on exact string matching against DB
        # In a real system, you'd use a Trie or explicit dictionaries.
        # Here we just iterate over known unique actors/directors/genres in DB.
        all_actors = set()
        all_directors = set()
        all_genres = set()
        
        for row in self.movies_db.values():
            for a in row.get('cast', '').split(','):
                if a.strip(): all_actors.add(a.strip())
            if row.get('director'): all_directors.add(row['director'].strip())
            for g in row.get('genres', '').split('|'):
                if g.strip(): all_genres.add(g.strip())
                
        for actor in all_actors:
            if self.normalize(actor) in norm_query:
                entities["actors"].append(actor)
        for director in all_directors:
            if self.normalize(director) in norm_query:
                entities["directors"].append(director)
        for genre in all_genres:
            if self.normalize(genre) in norm_query:
                entities["genres"].append(genre)
                
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', norm_query)
        if year_match:
            entities["years"].append(year_match.group(0))
            
        return entities

    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        The deterministic search pipeline.
        """
        norm_query = self.normalize(query)
        if not norm_query:
            return []
            
        # Alias Expansion
        if norm_query in ALIASES:
            norm_query = ALIASES[norm_query]
            
        entities = self.extract_entities(norm_query)
        
        results = []
        for iid, row in self.movies_db.items():
            norm_title = self.normalize(row.get('title', ''))
            norm_orig_title = self.normalize(row.get('original_title', ''))
            
            score = 0
            match_type = None
            
            # 1. Exact title match
            if norm_query == norm_title:
                score = 100
                match_type = "exact_title"
            # 2. Exact original title match
            elif norm_query == norm_orig_title:
                score = 95
                match_type = "exact_original_title"
            # 3. Partial title match (prefix or substring)
            elif norm_query in norm_title or norm_title.startswith(norm_query):
                score = 85
                match_type = "partial_title"
            else:
                # 4. Fuzzy title match
                fuzz_ratio = fuzz.token_sort_ratio(norm_query, norm_title)
                if fuzz_ratio >= 80:
                    score = fuzz_ratio
                    match_type = "fuzzy_title"
                    
            # Add score for entity matches if they exist
            if entities["actors"] and any(a in row.get('cast', '') for a in entities["actors"]):
                score = max(score, 70)
                if not match_type: match_type = "actor_match"
            if entities["directors"] and any(d in row.get('director', '') for d in entities["directors"]):
                score = max(score, 70)
                if not match_type: match_type = "director_match"
            if entities["genres"] and any(g in row.get('genres', '') for g in entities["genres"]):
                score = max(score, 50)
                if not match_type: match_type = "genre_match"
            if entities["years"] and row.get('year') in entities["years"]:
                score += 10 # slight boost for year match
                
            if score > 0:
                # Validation layer
                if self.validate(row):
                    results.append({
                        "item_id": iid,
                        "title": row.get('title'),
                        "poster_url": row.get('poster_url', ''),
                        "content_type": row.get('content_type', 'movie'),
                        "genres": row.get('genres', ''),
                        "year": row.get('year', ''),
                        "score": score,
                        "match_type": match_type
                    })
                    
        # Sort by deterministic ranking rules (score descending)
        results = sorted(results, key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def validate(self, row: dict) -> bool:
        """
        Validate metadata before returning.
        """
        if not row.get("item_id") or not row.get("title"):
            return False
        # Do not enforce poster_url for everything, but prefer it
        # Actually, prompt says: "Verify: Content ID, Metadata, Poster, Content Type, Genres, Release Year. Reject incomplete or broken records."
        if not row.get("poster_url"):
            return False
        if not row.get("genres"):
            return False
        if not row.get("year"):
            return False
        return True

    def autocomplete(self, query: str) -> List[Dict[str, str]]:
        """
        Extremely fast prefix/exact search for typeahead.
        """
        norm_query = self.normalize(query)
        if not norm_query:
            return []
            
        suggestions = []
        for iid, row in self.movies_db.items():
            norm_title = self.normalize(row.get('title', ''))
            
            # Prefix match
            if norm_title.startswith(norm_query):
                suggestions.append({
                    "text": row.get("title"),
                    "type": "title",
                    "id": iid
                })
                
        return suggestions[:5]
